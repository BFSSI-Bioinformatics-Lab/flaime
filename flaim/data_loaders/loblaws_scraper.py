import re
import time
import requests
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from django.conf import settings
from django_rq import job

# Selenium
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

# FLAIM
from flaim.database.nutrient_coding import EXPECTED_NUTRIENTS
from flaim.database import models

STATIC_ROOT = settings.STATIC_ROOT
MEDIA_ROOT = settings.MEDIA_ROOT

"""
TODO: 

-   Upon 400 Bad Request, close the browser window. 
    Example bad URL: https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Allergy-%26-Sinus/Allergy-%26-Sinus-Medicine/Jamieson-Multi-Vitamins%2C-100%-Complete%2C-Women-50-/p/20946029_EA

-   Continue to navigate through URLs until a product page is detected. Current scraper is too strict.
"""


class AccidentalRedirect(Exception):
    """ Raised when Selenium gets redirected from the intended URL """
    pass


class RecordExists(Exception):
    """ Raised when product code is already in the database """
    pass


def safe_run(func):
    """ Decorator to run a method wrapped in a try/except -> returns None upon exception """

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            return None

    return func_wrapper


@dataclass
class BaseScraper:
    """ Base class to load up the Selenium driver """
    url: str

    @staticmethod
    def load_driver():
        """
        Loads up Google Chrome with Selenium
        :return: WebDriver object
        """
        chrome_options = Options()
        chrome_options.add_argument("start-maximized")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        print(f"Loaded driver successfully: {driver}")
        return driver


@dataclass
class LoblawsSection(BaseScraper):
    # Loaded after class is initialized
    subcategory_urls: Optional[list] = None
    section_name: Optional[str] = None
    outdir: Path = Optional[None]

    def __post_init__(self):
        print(f"\nInitiated LoblawsSection object")
        self.driver = self.load_driver()

        # Pass URL to driver
        self.driver.get(self.url)

        # Wait for page to load
        print("Searching for element with product-image class to confirm page has loaded")
        _ = WebDriverWait(driver=self.driver, timeout=15).until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                                                "product-image")))

        # Get section name
        self.section_name = self.driver.find_element_by_class_name("row-hero-title").text.strip().upper()

        # Find subcategory links on the page
        subcategory_links = self.driver.find_elements_by_class_name("subcategory-link")

        # Extract the URL from each link
        print(f"Extracting link URLs for each subcategory on the page...")
        subcategory_urls = []
        for link in subcategory_links:
            try:
                subcategory_url = link.find_element_by_css_selector("a").get_attribute('href')
                subcategory_urls.append(subcategory_url)
            except NoSuchElementException as e:
                print(f"Couldn't extract <a> element from {link}")
                print(f"Traceback: {e}")

        self.subcategory_urls = subcategory_urls
        print(f"Found the following subcategory URLs:")
        [print(f"\t{x}") for x in self.subcategory_urls]

        # Exit window
        self.driver.quit()


@dataclass
class LoblawsSubcategory(BaseScraper):
    section: LoblawsSection

    # Default values
    total_products: int = 0
    max_products: int = 500
    product_urls: Optional[list] = None
    subcategory_name: Optional[str] = None
    outdir: Optional[Path] = None

    def __post_init__(self):
        print(f"\nInitiated LoblawsSubcategory object")
        self.driver = self.load_driver()

        # Pass URL to driver
        self.driver.get(self.url)

        # Wait for product tracking element to load (represents an individual product shown on the page grid)
        print("Waiting for elements to load...")
        try:
            _ = WebDriverWait(driver=self.driver, timeout=10).until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                                                    "product-tile__details")
                                                                                                   ))
        except:
            _ = WebDriverWait(driver=self.driver, timeout=10).until(ec.presence_of_element_located((By.CLASS_NAME,
                                                                                                    "product-info")
                                                                                                   ))

        # Update subcategory name
        self.subcategory_name = self.driver.find_element_by_class_name("page-title__title").text.strip().upper()

        # Grab the single load_more_button element on the page
        keep_clicking_load_button = True
        while keep_clicking_load_button and (self.total_products <= self.max_products):
            try:
                # Wait for the loading to complete
                _ = WebDriverWait(driver=self.driver, timeout=5).until(ec.presence_of_element_located(
                    (By.CLASS_NAME, "load-more-button")))

                load_more_button = self.driver.find_element_by_class_name("load-more-button")

                # Count # of products on the page so far, close out if it exceeds the maximum
                products_ = self.driver.find_elements_by_class_name("product-tile__details__info")
                if len(products_) > self.max_products:
                    print(f"Exceeded maximum number of products (max={self.max_products}), moving to next stage")
                    keep_clicking_load_button = False

                # Click the button
                print("Clicking load button...")
                load_more_button.click()
            except (NoSuchElementException, TimeoutException):
                keep_clicking_load_button = False
                print(f"Can't find the load button anymore - now aggregating all products on the page")

        # Product tiles contain 3 subclasses: __eyebrow, __thumbnail, and __details
        # (we only care about __details__info)
        products = self.driver.find_elements_by_class_name("product-tile__details__info")
        self.total_products = len(products)
        print(f"Detected {self.total_products} total products!")

        # Grab all of the urls on the page
        self.product_urls = [p.find_element_by_css_selector("a").get_attribute('href') for p in products]
        print(f"Found the following product URLs on the page:")
        [print(f"\t{x}") for x in self.product_urls]

        # Exit window
        self.driver.quit()

    def __repr__(self):
        return f"{self.subcategory_name}"


@dataclass
class ProductPage(BaseScraper):
    subcategory: LoblawsSubcategory
    outdir: Optional[Path] = None

    # Populated in __post_init__
    nutrition_present_flag: bool = False
    name: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[str] = None
    product_size: Optional[str] = None  # Total product size in grams
    breadcrumbs: Optional[str] = None  # Delimited by '>' symbol
    price: Optional[str] = None
    serving_size_raw: Optional[str] = None  # String value pulled straight from webpage; contains junk like '3/4 cup'
    serving_size: Optional[int] = None  # Integer value in g or mL parsed from serving_size_raw
    serving_size_units: Optional[str] = None  # either 'g' or 'mL'
    nutrition_dict: Optional[dict] = None
    image_paths: Optional[list] = None

    # Unique Loblaws 'Product Number'
    product_code: Optional[str] = None

    nutrition_element: Optional[WebElement] = None

    def __post_init__(self):
        print(f"Initiated ProductPage object with {self.url}")
        self.driver = self.load_driver()

        # Pass URL to driver
        self.driver.get(self.url)

        # Make sure we didn't get redirected
        if self.driver.current_url != self.url:
            raise AccidentalRedirect

        # Wait for page to load
        _ = WebDriverWait(driver=self.driver, timeout=10) \
            .until(ec.presence_of_element_located((By.CLASS_NAME, "product-name__item")))

        # Update the output directory for this instance
        self.name = self.get_product_name()
        self.product_code = self.get_product_code()

        self.outdir = self.outdir / f"{self.product_code}-{self.name.replace(' ', '_').replace(',', '')}"
        self.outdir.mkdir(exist_ok=True, parents=True)

        # Basic product page info
        self.product_size = self.get_product_size()
        self.brand = self.get_product_brand()
        self.price = self.get_product_price()
        self.breadcrumbs = self.get_product_breadcrumbs()
        self.description = self.get_product_description()
        self.ingredients = self.get_product_ingredients()

        # Nutrition parsing
        # Check for presence of nutrition table, if it's not available skip all downstream methods
        try:
            self.driver.find_element_by_class_name("product-details-page-info-layout--nutrition")
            self.nutrition_present_flag = True
        except NoSuchElementException:
            self.nutrition_present_flag = False

        if self.nutrition_present_flag:
            self.nutrition_element = self.get_product_nutrition_element()

            # Serving size information
            # Raw string
            self.serving_size_raw = self.get_serving_size(
                product_nutrition_element=self.nutrition_element)
            # Parse out the integer value and the units into a tuple
            serving_size, serving_size_units = self.parse_serving_size(self.serving_size_raw)
            # Update instance
            self.serving_size = serving_size
            self.serving_size_units = serving_size_units

            # Nutrition dictionary
            self.nutrition_dict = self.parse_product_nutrition_table(product_nutrition_element=self.nutrition_element)

        # Download all of the images for the product
        self.image_paths = []
        self.get_images()

        # Exit window
        self.driver.quit()

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def dump_to_tsv(self):
        outfile = self.outdir / f"{self.__repr__()}.tsv"
        with open(str(outfile), 'w') as f:
            f.write("attribute\tvalue\n")
            for attr, value in self:
                if attr == "image_paths":
                    value = "\t".join([str(x).replace(str(self.outdir.parent), "") for x in value])
                    f.write(f"{attr}\t{str(value)}\n")
                elif attr == "subcategory":
                    f.write(f"section\t{self.subcategory.section.section_name}\n")
                    f.write(f"subcategory\t{self.subcategory.subcategory_name}\n")
                elif attr == "description":
                    f.write(f'description\t"{value}"\n')
                else:
                    f.write(f"{attr}\t{str(value)}\n")

    def get_images(self):
        # Grab elements to click through
        try:
            image_dots = self.driver.find_element_by_class_name('slick-dots')
        # Close out early if there is only one image present for the product
        # TODO: Handling for cases where there is no image?
        except NoSuchElementException:
            zoom_button = self.driver.find_element_by_class_name('product-image-zoom-button')
            zoom_button.click()
            _ = WebDriverWait(driver=self.driver, timeout=3) \
                .until(ec.presence_of_element_located((By.CLASS_NAME, "product-image-zoom__image")))
            product_image = self.driver.find_element_by_class_name('responsive-image--product-image-zoom')
            image_url = product_image.get_attribute('src')
            self.save_image(url=image_url, outdir=self.outdir)
            return

        dot_list = image_dots.find_elements_by_xpath('li')
        image_urls = []

        # Iterate over each image in the set
        for dot in dot_list:
            dot.click()
            time.sleep(0.5)
            zoom_button = self.driver.find_element_by_class_name('product-image-zoom-button')
            zoom_button.click()
            _ = WebDriverWait(driver=self.driver, timeout=3) \
                .until(ec.presence_of_element_located((By.CLASS_NAME, "product-image-zoom__image")))
            product_image = self.driver.find_element_by_class_name('responsive-image--product-image-zoom')
            image_url = str(product_image.get_attribute('src'))
            image_urls.append(image_url)
            close_button = self.driver.find_element_by_class_name('modal-dialog__content__close')
            close_button.click()

        # Save images to outdir
        print("Saving the following images:")
        [print(img) for img in image_urls]
        if len(image_urls) > 0:
            for img in image_urls:
                self.save_image(url=img, outdir=self.outdir)

    def save_image(self, url: str, outdir: Path):
        """
        Uses requests to save the url of an image
        :param url: path to an image you want to save
        :param outdir: directory where you want to save the file
        :return:
        """
        outfile = outdir / Path(url).name.replace("%", "")
        print(f"Saving {url} to {outfile}")
        r = requests.get(url)
        with open(str(outfile), "wb") as f:
            for chunk in r:
                f.write(chunk)
        if self.image_paths is not None:
            self.image_paths.append(outfile)

    # Required so no safe-run
    def get_product_code(self):
        product_code = self.driver.find_element_by_class_name('product-number__code').text.strip()
        return product_code

    # Required so no safe-run
    def get_product_name(self):
        product_name = self.driver.find_element_by_class_name('product-name__item--name').text.strip()
        return product_name

    @safe_run
    def get_product_size(self):
        product_size = self.driver.find_element_by_class_name('product-name__item--package-size').text.strip()
        return product_size

    @safe_run
    def get_product_price(self):
        product_price = self.driver.find_element_by_class_name(
            'selling-price-list__item__price--now-price').text.strip()
        print(f"Found the following product price: {product_price}")
        return product_price

    @safe_run
    def get_product_brand(self):
        product_brand = self.driver.find_element_by_class_name('product-name__item--brand').text.strip()
        return product_brand

    @safe_run
    def get_product_breadcrumbs(self):
        product_breadcrumbs = self.driver.find_element_by_class_name('breadcrumbs').text
        product_breadcrumbs = product_breadcrumbs.replace("\n", ">").upper()  # Clean up the formatting
        return product_breadcrumbs

    @safe_run
    def get_product_description(self):
        product_description = self.driver.find_element_by_class_name(
            'product-description-text__text').text.upper().strip()
        return product_description

    @safe_run
    def get_product_ingredients(self):
        product_ingredients = self.driver.find_element_by_class_name(
            'product-details-page-info-layout--ingredients').text.upper()
        product_ingredients = product_ingredients.replace("INGREDIENTS", "").strip()
        return product_ingredients

    @safe_run
    def get_product_nutrition_element(self) -> WebElement:
        """
        Gets the product-nutition element on the page which contains the following subelements:
            product-nutrition__food-labels
            product-nutrition__nutrients-per-serving-table
            product-nutrition__disclaimer
        """
        product_nutrition = self.driver.find_element_by_class_name('product-nutrition')
        return product_nutrition

    @staticmethod
    def get_serving_size(product_nutrition_element):
        serving_size = product_nutrition_element.find_element_by_class_name("nutritional-value-list").text
        serving_size = serving_size.strip()
        return serving_size

    @staticmethod
    def parse_serving_size(serving_size: str) -> tuple:
        """
        Uses regex to extract either grams or mL value from string
        Example input data:
            Serving Size grams 30 g
            Serving Size grams per 3/4 cup (30 g)
            Serving Size grams PER 1/4 CUP (60 ml)
        Desired output:
            30
            30
            60
        """
        # Cast to lowercase
        serving_size = serving_size.lower()
        # Capture things like '30 g' and '60mL' then strip out characters we don't care about
        match = re.search(r'[0-9]{1,4}\s*[gm]', serving_size)
        match = match.group()

        # Extract the units for the value
        unit = None
        if 'g' in match:
            unit = 'g'
        elif 'm' in match:
            unit = 'mL'

        match = match.replace("g", "").replace("m", "").strip()
        return int(match), unit

    def get_nutrients_per_serving_columns(self) -> list:
        """
        Will grab all of the nutrition columns available for the product.
        Raises an exception if there aren't any.
        """
        nutrients_per_serving = self.driver.find_elements_by_class_name(
            "product-nutrition__nutrients-per-serving-column"
        )
        assert len(nutrients_per_serving) >= 1
        return nutrients_per_serving

    @staticmethod
    def parse_product_nutrition_table(product_nutrition_element: WebElement) -> dict:
        """ Parses the product-nutrition element """
        table_text = product_nutrition_element.text.split("\n")
        print(f"Table text: {table_text}")

        # Make a copy of the global tuple, coerce to list so we can delete entries on the go
        expected_nutrients_ = list(EXPECTED_NUTRIENTS)

        nutrition_dict: dict = {}
        current_nutrient = None
        for line in table_text:
            for i, exp in enumerate(expected_nutrients_):
                if exp in line:
                    current_nutrient = line

                    # Hacky method of normalizing spelling of fiber vs. fibre (fibre is preferred)
                    if 'iber' in current_nutrient.lower():
                        current_nutrient = current_nutrient.replace("iber", "ibre")
                    nutrition_dict[current_nutrient] = []
                    expected_nutrients_.pop(i)
                    continue

            # TODO: It seems like sometimes there is only a %DV and no other value
            """
            Example:
            https://www.loblaws.ca/Food/Pantry/Breakfast/Oatmeal-%26-Hot-Cereals/Stoked-Oats-Stone-Age-Bag/p/20971534_EA
            """

            # Check if it's a unit line. We'll put it into the nutrition dictionary if it is.
            if any(x in line.lower() for x in [' %', ' g', ' mg', ' cal']) and current_nutrient is not None:
                line = line.replace(",", ".")  # Sometimes a comma is used in place of a decimal
                nutrition_dict[current_nutrient].append(line)

        print(f"Nutrition dictionary:")
        for key, val in nutrition_dict.items():
            print(f"{key}: {val}")

        return nutrition_dict

    def __repr__(self):
        return f"{self.product_code}_{self.name}_({self.brand})"


def check_if_product_exists(product_code: str) -> bool:
    return models.Product.objects.filter(product_code=product_code).exists()


def update_database(product: ProductPage):
    # Create the base product in the database
    base_product_instance = models.Product.objects.create(name=product.name,
                                                          brand=product.brand,
                                                          store='LOBLAWS',
                                                          product_code=product.product_code,
                                                          nutrition_available=product.nutrition_present_flag,
                                                          price=product.price,
                                                          url=product.url)
    base_product_instance.save()

    # Create and populate the nutrition facts instance
    nutrition_facts_instance = models.NutritionFacts.objects.create(product=base_product_instance,
                                                                    total_size=product.product_size,
                                                                    serving_size_raw=product.serving_size_raw,
                                                                    serving_size=product.serving_size,
                                                                    serving_size_units=product.serving_size_units,
                                                                    ingredients=product.ingredients,
                                                                    nutrition_raw_text=str(product.nutrition_dict))
    if product.nutrition_dict is not None:
        nutrition_facts_instance = nutrition_dict_to_nutrition_facts_instance(product_page=product,
                                                                              nutrition_facts_instance=nutrition_facts_instance)
    nutrition_facts_instance.save()

    # Create Loblaws product instance
    loblaws_product_instance = models.LoblawsProduct.objects.create(
        product=base_product_instance,
        subcategory=product.subcategory.subcategory_name,
        section=product.subcategory.section.section_name,
        description=product.description,
        image_directory=str(product.outdir),  # TODO: Strip MEDIA_ROOT from this variable
        breadcrumbs=product.breadcrumbs
    )
    loblaws_product_instance.save()

    # Iterate over images and create ProductImage records
    generate_product_image_records(image_dir=product.outdir, product_instance=base_product_instance)

    print(f"Successfully added records for {product.product_code} to FLAIM-DB")


def nutrition_dict_to_nutrition_facts_instance(product_page: ProductPage,
                                               nutrition_facts_instance: models.NutritionFacts):
    """
    This iterates over the product nutrition dictionary, and performs unit conversion where necessary (mg -> g),
    parses out what is a quantitative value and what is a % DV, and then updates the Nutrition Facts model instance
    with all of that data for every single nutrient in the dictionary.
    """
    for nutrient, vals in product_page.nutrition_dict.items():
        # [vals] is either 1 or 2 items long -> need to separate DV and value

        # Normalize the dict keys to match the columns in the database
        nutrient = nutrient.lower().replace(" ", "_").replace(".", "")

        # Make sure the nutrient is something we're expecting
        if nutrition_facts_instance.valid_nutrient(nutrient):

            # Parse out DV from regular value
            nutrient_dv_raw = None
            nutrient_value_raw = None
            print(f"Parsing {vals} into value and DV")
            for val in vals:
                if '%' in val:
                    print(f"{val} -> DV")
                    nutrient_dv_raw = val
                else:
                    print(f"{val} -> value")
                    nutrient_value_raw = val

            # Set the nutrition_value (e.g. 9g total fat)
            if nutrient_value_raw is not None:
                nutrient_value, unit = nutrition_facts_instance.extract_number_from_nutrient(nutrient_value_raw)
                setattr(nutrition_facts_instance, nutrient, nutrient_value)

            # Set the DV (e.g. 5 %)
            if nutrient_dv_raw is not None:
                nutrient_value_dv, unit = nutrition_facts_instance.extract_number_from_nutrient(nutrient_dv_raw)
                setattr(nutrition_facts_instance, f"{nutrient}_dv", nutrient_value_dv)
    return nutrition_facts_instance


def generate_product_image_records(image_dir: Path, product_instance: models.Product):
    """
    Have to strip out the MEDIA_ROOT from the file paths to behave properly with FileField/ImageField
    """
    images = [str(x).replace(settings.MEDIA_ROOT + "/", "") for x in list(image_dir.glob("*")) if x.is_file()]
    for i in images:
        models.ProductImage.objects.create(product=product_instance,
                                           image_path=i)


@job('high')
def run_loblaws_scraper(url: str, outdir: Path, filter_keyword: str = None, load_into_db: bool = True,
                        dump_to_csv: bool = False):
    print(f"Started Loblaws Scraper")

    # Get the scraper going -> outdir should always follow /{MEDIA_ROOT}/{store}/{YYYYMMDD}/ pattern
    outdir = outdir / 'LOBLAWS' / time.strftime('%Y%m%d')
    section = LoblawsSection(url=url, outdir=outdir)

    product_objects = []
    for subcategory_url in section.subcategory_urls:
        subcategory = LoblawsSubcategory(url=subcategory_url,
                                         outdir=section.outdir,
                                         section=section)

        # Filter's out results if they don't contain the keyword, e.g. 'CEREAL'
        if filter_keyword is not None:
            if filter_keyword not in subcategory.subcategory_name.upper():
                continue

        # Ping the DB to see if we already have a product, remove it from the list if it exists
        filtered_product_urls = []
        for product_url in subcategory.product_urls:
            product_code = Path(product_url).name
            if check_if_product_exists(product_code=product_code) is True:
                print(f"{product_code} already exists, skipping")
            else:
                filtered_product_urls.append(product_url)

        existing_products = list(outdir.glob("**"))
        existing_products = [x for x in existing_products if x.is_dir()]
        existing_product_codes = [x.name.split("-")[0] for x in existing_products]
        print(f"Detected {len(existing_product_codes)} total existing product codes in {outdir}")
        filtered_product_urls = [x for x in filtered_product_urls if Path(x).name not in existing_product_codes]

        # Extract information from each product URL with Selenium
        print(f"Scraping {len(filtered_product_urls)} total products for {subcategory.subcategory_name}")
        for product_url in filtered_product_urls:
            try:
                product = ProductPage(url=product_url, outdir=subcategory.outdir,
                                      subcategory=subcategory)
            except AccidentalRedirect:
                print(f"Loblaws redirect detected; skipping {product_url}")
                continue
            except Exception as e:
                print(f"Encountered some other strange exception for {product_url}, skipping...")
                print(e)
                continue

            product_objects.append(product)

            # Load Product data into Postgres
            if load_into_db:
                update_database(product=product)
            else:
                # Procedures to dump output to CSV files
                if dump_to_csv:
                    product.dump_to_tsv()
            print(f"Done with product '{product.name}'")
