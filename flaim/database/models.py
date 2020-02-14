from time import strftime
from pathlib import Path
from django.db import models
from typing import Optional, Union
from django.conf import settings
from django.contrib.postgres.fields import JSONField, ArrayField
from flaim.database.nutrient_coding import VALID_NUTRIENT_COLUMNS
from simple_history.models import HistoricalRecords


def upload_product_image(obj):
    """ Sets the directory for an input ProductImage """
    store = obj.product.store
    date = strftime("%Y%m%d")
    return f"{store}/{date}"


def upload_fop_image(obj):
    """
    Note: obj must be instance of ProductImage model

    Takes the parent product_image name e.g. /LOBLAWS/20190101/something.jpg and morphs it into
    /LOBLAWS/20190101/something_fop.jpg

    Reference for how ImageField attributes can be accessed:
    https://docs.djangoproject.com/en/2.2/topics/files/
    """
    parent_path = Path(obj.product_image.image_path.name)  # e.g. /LOBLAWS/20190101/something.jpg
    suffix = parent_path.suffix
    fop_path = parent_path.with_suffix(f'_FOP{suffix}')
    return fop_path


def safe_run(func):
    """ Decorator to run a method wrapped in a try/except -> returns None upon exception """

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return None

    return func_wrapper


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    updating ``created`` and ``modified`` fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# GENERAL MODELS
class ScrapeBatch(models.Model):
    """
    Upon submission of a scraping job, that job is assigned an ID using this table and any products collected throughout
    the job will be nested beneath it.
    """
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)  # Should be populated manually once scrape job is complete
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Scrape Batch'
        verbose_name_plural = 'Scrape Batches'


class Product(TimeStampedModel):
    product_code = models.CharField(max_length=500)
    name = models.CharField(max_length=500, unique=False, blank=True, null=True)
    brand = models.CharField(max_length=500, blank=True, null=True)

    # TODO: Make batch field required upon instantiation once we move towards a more production-ready version of FLAIME
    batch = models.ForeignKey(ScrapeBatch, on_delete=models.CASCADE, blank=True, null=True)

    # TODO: Move loblaws_product description field here
    # product_description = models.TextField(blank=True, null=True)

    VALID_STORES = (
        ('LOBLAWS', 'Loblaws'),
        ('WALMART', 'Walmart'),
        ('AMAZON', 'Amazon')
    )
    store = models.CharField(max_length=7, choices=VALID_STORES)
    price = models.CharField(max_length=200, blank=True, null=True)
    price_float = models.FloatField(blank=True, null=True)
    price_units = models.CharField(max_length=20, blank=True, null=True)
    upc_code = models.CharField(max_length=500, blank=True, null=True)
    manufacturer = models.CharField(max_length=500, blank=True, null=True)  # e.g. from Amazon technical details
    nutrition_available = models.BooleanField(blank=True, null=True)
    url = models.URLField(max_length=1000, blank=True, null=True)
    scrape_date = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product_code}: {self.name}"

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=['product_code'])
        ]


class NutritionFacts(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="nutrition_facts")
    total_size = models.CharField(max_length=200, blank=True,
                                  null=True)  # Should be serving_size * # of servings in product
    serving_size_raw = models.CharField(max_length=200, blank=True, null=True)  # Unparsed serving size text
    serving_size = models.IntegerField(blank=True, null=True)  # Parsed numeric serving size value

    SERVING_SIZE_UNITS = (
        ('g', 'grams'),
        ('mL', 'millilitres')
    )
    serving_size_units = models.CharField(max_length=11, choices=SERVING_SIZE_UNITS, blank=True, null=True)

    ingredients = models.TextField(blank=True, null=True)

    # Nutrients - units should always be represented as grams
    calories = models.IntegerField(blank=True, null=True)
    sodium = models.FloatField(blank=True, null=True)
    sodium_dv = models.FloatField(blank=True, null=True)
    calcium = models.FloatField(blank=True, null=True)
    calcium_dv = models.FloatField(blank=True, null=True)
    totalfat = models.FloatField(blank=True, null=True)
    totalfat_dv = models.FloatField(blank=True, null=True)
    monounsaturated_fat = models.FloatField(blank=True, null=True)
    polyunsaturated_fat = models.FloatField(blank=True, null=True)
    omega3fattyacids = models.FloatField(blank=True, null=True)
    saturatedfat = models.FloatField(blank=True, null=True)
    saturatedfat_dv = models.FloatField(blank=True, null=True)
    transfat = models.FloatField(blank=True, null=True)
    transfat_dv = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    potassium_dv = models.FloatField(blank=True, null=True)
    totalcarbohydrate = models.FloatField(blank=True, null=True)
    totalcarbohydrate_dv = models.FloatField(blank=True, null=True)
    othercarbohydrates = models.FloatField(blank=True, null=True)
    dietaryfiber = models.FloatField(blank=True, null=True)
    dietaryfiber_dv = models.FloatField(blank=True, null=True)
    sugar = models.FloatField(blank=True, null=True)
    protein = models.FloatField(blank=True, null=True)
    cholesterol = models.FloatField(blank=True, null=True)
    vitamina = models.FloatField(blank=True, null=True)
    vitamina_dv = models.FloatField(blank=True, null=True)
    vitaminc = models.FloatField(blank=True, null=True)
    vitaminc_dv = models.FloatField(blank=True, null=True)
    vitamind = models.FloatField(blank=True, null=True)
    vitamine = models.FloatField(blank=True, null=True)
    niacin = models.FloatField(blank=True, null=True)
    vitaminb6 = models.FloatField(blank=True, null=True)
    folacin = models.FloatField(blank=True, null=True)
    folate = models.FloatField(blank=True, null=True)
    vitaminb12 = models.FloatField(blank=True, null=True)
    pantothenicacid = models.FloatField(blank=True, null=True)
    pantothenate = models.FloatField(blank=True, null=True)
    alcohol = models.FloatField(blank=True, null=True)
    carbohydrate = models.FloatField(blank=True, null=True)
    erythritol = models.FloatField(blank=True, null=True)
    glycerol = models.FloatField(blank=True, null=True)
    isomalt = models.FloatField(blank=True, null=True)
    lactitol = models.FloatField(blank=True, null=True)
    maltitol = models.FloatField(blank=True, null=True)
    mannitol = models.FloatField(blank=True, null=True)
    polydextrose = models.FloatField(blank=True, null=True)
    sorbitol = models.FloatField(blank=True, null=True)
    xylitol = models.FloatField(blank=True, null=True)
    iron = models.FloatField(blank=True, null=True)
    iron_dv = models.FloatField(blank=True, null=True)
    riboflavin = models.FloatField(blank=True, null=True)
    selenium = models.FloatField(blank=True, null=True)
    magnesium = models.FloatField(blank=True, null=True)
    phosphorus = models.FloatField(blank=True, null=True)
    thiamine = models.FloatField(blank=True, null=True)
    zinc = models.FloatField(blank=True, null=True)

    nutrition_raw_text = models.TextField(blank=True, null=True)

    history = HistoricalRecords()

    def load_ingredients(self, api_data: dict):
        self.ingredients = api_data['ingredients']
        self.save()

    def load_total_size(self, api_data: dict):
        self.total_size = api_data['packageSize']
        self.save()

    def load_loblaws_nutrition_facts_json(self, loblaws_nutrition: dict):
        """
        Given LoblawsProduct.nutrition_facts_json field, will parse out all nutrients and dump data into this model
        """
        # Grab nutrients available in the NutritionFacts model
        nutritionfacts_model = NutritionFacts()
        nutrition_facts_attributes = list(vars(nutritionfacts_model))

        # Parse food labels (serving size, calories, calories from fat?).
        # Loop over and validate code to ensure we get the right data.
        if 'foodLabels' in loblaws_nutrition:
            for item in loblaws_nutrition['foodLabels']:
                if item['code'] == 'perservesizeamt':
                    self.serving_size_raw = item['valueInGram'].strip()
                    self.serving_size_units = self.__detect_units(self.serving_size_raw.lower())
                if item['code'] == 'calories':
                    # This is the correct key; just seems to be a naming error in the API
                    self.calories, unit = self.__extract_number_from_nutrient(item['valueInGram'])

        # Parse the nutrientsPerServing, micronutrients, and subNutrients sections. Flatten into a 1-D list.
        nutrient_json = loblaws_nutrition['nutrientsPerServing'] + loblaws_nutrition['micronutrients']
        for n in nutrient_json:
            if n['subNutrients'] is not None:
                nutrient_json += n['subNutrients']

        # Verify that expected nutrient keys are present, extract matching model values
        nutrient_error_detected = False
        if any(x in ('nutrientsPerServing', 'micronutrients') for x in loblaws_nutrition):
            for n in nutrient_json:
                nutrient = n['code']
                if nutrient in nutrition_facts_attributes:  # Attributes for the NutritionFacts model
                    # Actual nutrient value
                    if n['valueInGram']:
                        try:
                            val, unit = self.__extract_number_from_nutrient(n['valueInGram'])
                            setattr(self, nutrient, val)
                        except TypeError as e:
                            nutrient_error_detected = True

                    # Percent DV
                    if n['valuePercent']:
                        try:
                            val, unit = self.__extract_number_from_nutrient(n['valuePercent'])
                            if unit != '%':
                                print(f'Error detected for percent DV of {nutrient} -> found {val, unit}. '
                                      f'Setting values to null.')
                                val, unit = None, None
                            setattr(self, (nutrient + '_dv'), val)
                        except TypeError as e:
                            nutrient_error_detected = True

        if nutrient_error_detected:
            print(f'Detected an error for {self.product} when parsing nutrition facts')

        self.save()

    @staticmethod
    def __detect_units(val: str) -> Optional[str]:
        """
        Method to detect units in a nutrient value string. Expects .lower() to be calleded on the input value already

        TODO: This is a super fragile implementation. The order of the if statements is very important, and there is
            some sketchy implicit logic that isn't clear, e.g. `if 'k' in val` covers both 'kCal' and 'k', and will
            then split on 'k' to extract the numeric value

        :param val: string for nutrient value e.g. 30 g, 50 cal, 500 mg,  etc.
        :return: string containing units for input value - this is the value that will be split on when extracting
                numeric values
        """
        if any(x in ['<', '>', '<=', '>='] for x in val):  # This junk shows up on rare occasions - ignore it
            return None
        # Milligrams
        elif 'mg' in val:
            return 'mg'
        elif 'milligrams' in val:
            return 'milligrams'
        # mL / millilitres
        elif 'ml' in val:
            return 'ml'
        elif 'millilitres' in val:
            return 'millilitres'
        # calories / cal
        elif 'k' in val:
            return 'k'
        elif 'cal' in val:
            return 'cal'
        # % DV
        elif '%' in val:
            return '%'
        elif 'dv' in val:
            return 'dv'
        # Grams
        elif 'g' in val or 'grams' in val:
            return 'g'
        elif 'l' in val or 'litres' in val:
            return 'l'
        else:
            print(f"WARNING: Could not detect any units in value ({val})")
            return None

    def __extract_number_from_nutrient(self, val: str) -> Union[tuple, None]:
        """
        Given an input nutrient string, will return the float value while handling unit conversion if necessary
        """
        if val is None:
            return None

        # Check to see if the units are missing, but there is a numeric value. Just toss the data in this case.
        if val.isnumeric():
            return None

        # Grab the units from the nutrient string
        val = val.lower()
        nutrient_type = self.__detect_units(val)
        if nutrient_type is None:
            return None

        # Grab the numeric float value from the string
        try:
            nutrient_float = float(val.split(nutrient_type)[0].strip())
        except ValueError as e:
            print(val)
            print(nutrient_type)
            raise e

        # Grams & Milligrams (normalizes everything into grams)
        if nutrient_type == 'g':
            return nutrient_float, 'g'
        elif nutrient_type == 'mg' or nutrient_type == "milligrams":
            return self.__convert_milligrams_to_grams(nutrient_float), 'g'

        # Percent DV (values on nutrition labels are integers ranging from 0% -> n%, so we convert to float)
        if nutrient_type == "dv" or nutrient_type == "%":
            return float(nutrient_float / 100), '%'

        # Calories
        if nutrient_type == "cal" or nutrient_type == "calories" or nutrient_type == "k":
            return int(nutrient_float), 'cal'
        return None

    @staticmethod
    def __convert_milligrams_to_grams(val: float) -> float:
        return val * 0.001

    @staticmethod
    def __valid_nutrient(nutrient: str) -> bool:
        # Grab list of attributes
        if nutrient in VALID_NUTRIENT_COLUMNS:
            print(f"Detected '{nutrient}'")
            return True
        else:
            print(f"Value '{nutrient}' is not a valid database column")
            return False

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Product Nutrition'
        verbose_name_plural = 'Product Nutrition'


# LOBLAWS MODELS

class LoblawsProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Loblaws specific metadata
    """

    # This data was scraped from Loblaws with Selenium
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="loblaws_product")
    description = models.TextField(blank=True, null=True)
    # TODO: Implement upload_to for image_directory because right now the paths are stored as straight up strings
    #  including the root. This is not portable at all and will cause issues whenever the server migration occurs.
    image_directory = models.CharField(max_length=1200, blank=True, null=True)
    upc_list = ArrayField(models.CharField(max_length=300), blank=True, null=True)
    breadcrumbs_text = models.CharField(max_length=600, blank=True, null=True)
    breadcrumbs_array = ArrayField(models.CharField(max_length=300), blank=True, null=True)
    nutrition_facts_json = JSONField(blank=True, null=True)

    # This JSON data is retrieved from the API. See flaim.data_loaders.loblaws.product_detail_api.py
    api_data = JSONField(blank=True, null=True)

    def json_to_fields(self):
        if self.api_data is not None:
            self.breadcrumbs_array = self.get_breadcrumbs()
            self.description = self.get_description()
            self.upc_list = self.get_upc_list()
            self.nutrition_facts_json = self.get_nutrition_facts()
            self.save()

            self.product.store = 'LOBLAWS'
            self.product.name = self.get_name()

            if self.upc_list is not None:
                self.product.upc_code = self.get_upc_list()[0]

            self.product.brand = self.get_brand()
            self.product.ingredients = self.get_ingredients()
            self.product.price_float, self.product.price_units = self.get_price()
            self.product.url = self.get_link()
            self.product.save()

    @safe_run
    def get_name(self) -> str:
        """ Returns plain text; every product should have a name value """
        return self.api_data['name'].strip()

    @safe_run
    def get_brand(self) -> str:
        """ Returns plain text """
        return self.api_data['brand'].strip()

    @safe_run
    def get_description(self) -> str:
        """ Return the product description, often including HTML tags as well as plain text """
        return self.api_data['description'].strip()

    @safe_run
    def get_all_image_urls(self) -> list:
        """ This will retrieve ALL of the image urls associated with the product; more than we need """
        return self.api_data['imageAssets']

    @safe_run
    def get_large_image_urls(self):
        """ This is typically the image data we want to retrieve per product """
        images = [x['largeUrl'] for x in self.api_data['imageAssets']]
        return images

    @safe_run
    def get_package_size(self) -> str:
        return self.api_data['packageSize'].strip()

    @safe_run
    def get_link(self) -> str:
        """ Returns the link to the product on the Loblaws domain; no guarantee the link is still accurate/active """
        return 'https://www.loblaws.ca' + self.api_data['link'].strip()

    def get_price(self) -> (int, str):
        """ Concatenates the price and unit values to produce something like '$6.99 ea' """
        try:
            price, unit = float(self.api_data['prices']['price']['value']), self.api_data['prices']['price']['unit']
        except (TypeError, KeyError) as e:
            print(f'Could not retrieve price for {self.product}')
            price, unit = None, None
        return price, unit

    @safe_run
    def get_country_of_origin(self) -> str:
        return self.api_data['countryOfOrigin'].strip()

    @safe_run
    def get_ingredients(self) -> str:
        return self.api_data['ingredients'].strip()

    @safe_run
    def get_nutrition_facts(self):
        # All information is stored in nutritionFacts
        nutrition_facts = self.api_data['nutritionFacts']

        # Further parsing out nutritionFacts
        '''
        List containing serving size, calories, etc
        '''
        food_labels = nutrition_facts['foodLabels']

        '''
        List containing nutrients with values in grams and percent.
        Values in here can contain additional subnutrients e.g. totalfat -> saturatedfat, polyunsaturatedfat
        '''
        nutrients_per_serving = nutrition_facts['nutrientsPerServing']

        '''
        List containing micronutrients e.g. vitamin A, vitamin C, iron
        '''
        micronutrients = nutrition_facts['micronutrients']

        '''
        Text with nutrition disclaimer that the data is approximate and not necessarily accurate
        '''
        disclaimer = nutrition_facts['disclaimer']

        '''
        This field is not necessarily populated
        '''
        ingredients = nutrition_facts['ingredients']

        '''
        Not sure what this is for, comes up as empty string mostly
        '''
        nutrition_heading = nutrition_facts['nutritionHeading']

        return nutrition_facts

    @safe_run
    def get_nutrition_facts_list(self):
        # TODO: Figure out what this field is used for, comes up as empty list mostly?
        pass

    @safe_run
    def get_health_tips(self) -> str:
        return self.api_data['healthTips'].strip()

    @safe_run
    def get_safety_tips(self) -> str:
        return self.api_data['safetyTips'].strip()

    @safe_run
    def get_breadcrumbs(self) -> list:
        """
        :return:    Returns list of of breadcrumbs in order from highest level to lowest level e.g.
                    [Food, Fruits & Vegetables, Fruit, Apples]
        """
        breadcrumbs = self.api_data['breadcrumbs']
        breadcrumb_names = [x['name'].strip() for x in breadcrumbs]
        return breadcrumb_names

    @safe_run
    def get_upc_list(self) -> list:
        return [x.strip() for x in self.api_data['upcs']]

    @safe_run
    def get_average_weight(self) -> str:
        return self.api_data['averageWeight'].strip()

    @safe_run
    def get_nutrition_disclaimer(self) -> str:
        return self.api_data['productNutritionDisclaimer'].strip()

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Loblaws Product'
        verbose_name_plural = 'Loblaws Products'
        indexes = [
            models.Index(fields=['product'])
        ]

    history = HistoricalRecords()


# WALMART MODELS

class WalmartProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Walmart specific metadata
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="walmart_product")
    image_directory = models.CharField(max_length=500, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Walmart Product'
        verbose_name_plural = 'Walmart Products'


# AMAZON MODELS

class AmazonProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Amazon specific metadata
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="amazon_product")
    bullet_points = models.TextField(null=True, blank=True)  # The Amazon description field
    manufacturer_reference = models.CharField(max_length=100, blank=True,
                                              null=True)  # e.g. from Amazon technical details
    speciality = models.CharField(max_length=100, blank=True, null=True)  # e.g. Kosher
    units = models.CharField(max_length=30, blank=True, null=True)  # e.g. 2.5 Kilograms
    item_weight = models.CharField(max_length=30, blank=True, null=True)  # e.g. 1.58 kg
    parcel_dimensions = models.CharField(max_length=30, blank=True, null=True)  # e.g. 30 x 30 x 30 cm
    date_first_available = models.DateField(null=True, blank=True)  # from the Additional Information table
    image_directory = models.CharField(max_length=1000, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Amazon Product'
        verbose_name_plural = 'Amazon Products'


class AmazonSearchResult(TimeStampedModel):
    """
        Stores information on the search page that a particular product showed up on
    """
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_search_result")
    search_string = models.CharField(max_length=500)  # Search string used to generate results
    page = models.IntegerField()  # Page that the product showed up on
    item_number = models.IntegerField()  # Of products shown on search page, tracks the index of the product (i.e. 2nd)

    class Meta:
        verbose_name = 'Amazon Search Result'
        verbose_name_plural = 'Amazon Search Results'


class AmazonProductReview(TimeStampedModel):
    """
        Model to store information on a single Amazon product review
    """
    # One Amazon Product will have many reviews
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_product_reviews")
    review_title = models.CharField(max_length=300)
    review_text = models.TextField(blank=True, null=True)
    reviewer_username = models.CharField(max_length=100)
    rating = models.FloatField()  # e.g. 3 out of 5 stars -> convert to float
    helpful = models.BooleanField()  # Flag for if the review was marked as helpful or not by Amazon

    class Meta:
        verbose_name = 'Amazon Product Review'
        verbose_name_plural = 'Amazon Product Reviews'


# IMAGE CLASSIFICATION
class ProductImage(TimeStampedModel):
    """
        Model to store relationship between a Product and a path to a product image
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_image")
    image_path = models.ImageField(upload_to=upload_product_image, unique=True, max_length=1200)
    image_number = models.IntegerField(blank=True, null=True)  # Order of the image in a set for a product

    def __str__(self):
        return f"{self.product}: {Path(self.image_path.url).name}"

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'


class NutritionLabelClassification(TimeStampedModel):
    """
        Stores output from the nutrition label classifier for a ProductImage
    """
    # Required fields
    product_image = models.ForeignKey(ProductImage, on_delete=models.CASCADE, related_name="image_classification")

    # Classification can be populated after the fact as it can take time to calculate
    classification_choices = (
        ('N', 'NUTRITION'),
        ('I', 'INGREDIENTS'),
        ('O', 'OTHER'),
    )
    classification = models.CharField(choices=classification_choices, max_length=15, null=True, blank=True)

    class Meta:
        verbose_name = 'Image Classification'
        verbose_name_plural = 'Image Classifications'


class FrontOfPackLabel(TimeStampedModel):
    """
    Stores output from the FrontOfPackLabel classifier
    """
    product_image = models.OneToOneField(ProductImage, on_delete=models.CASCADE, related_name="fop_label")

    # Results from the classifier should be available in a simple JSON object
    classifier_result_json = JSONField(blank=True, null=True)

    # Boolean to represent if a FOP label is present or not
    label_detected = models.BooleanField()

    # TODO: Figure out what kind of classifications we can nail down with the model
    label_type_choices = (
        ('FC', 'FOOD_COLOURING'),
    )
    label_type = models.CharField(max_length=30, choices=label_type_choices, null=True, blank=True)
    classified_image_path = models.ImageField(upload_to=upload_fop_image, max_length=1000)

    def __str__(self):
        return f"{self.product_image.product.name} - FOP Present: {self.label_detected}"

    @property
    def classified_image_filename(self):
        return Path(self.classified_image_path.path).name

    class Meta:
        verbose_name = 'FOP Label'
        verbose_name_plural = 'FOP Labels'
