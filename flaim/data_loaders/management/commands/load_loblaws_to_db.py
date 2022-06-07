import json
from pathlib import Path
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from tqdm import tqdm
import re

from flaim.database.models import Product, LoblawsProduct, NutritionFacts, ScrapeBatch, ProductImage
from flaim.classifiers.management.commands.assign_categories import assign_categories
from flaim.data_loaders.management.commands.calculate_atwater import calculate_atwater
from flaim.data_loaders.management.accessories import assign_variety_pack_flag

User = get_user_model()


# TODO: Implement automatic scanning/calling of this script upon finding new data

def normalize_apostrophe(val: str):
    """
    Values like brand and name often have inconsistent apostrophes: this method should be applied to name and brand
    before upload to the database. This is especially important for matching products by brand.
    :param val: string to swap apostrophes on
    :return: new string with proper apostrophe
    """
    if val is None:
        return None
    old_apostrophe = "’"
    new_postrophe = "'"
    return val.replace(old_apostrophe, new_postrophe)


def read_json(json_file):
    """
    Updated to account for the scrapy output files
    """
    try:
        with open(json_file) as f:
            products = json.load(f)
    except:
        # Scrapy output json is a bit different
        products = []
        with open(json_file, 'r') as f:
            for line in f:
                line = line.rstrip("\n")
                line = line.rstrip(",")
                line = line.rstrip("[")
                line = line.rstrip("]")
                if (line == "[") | (line == "]") | (line == "]["):
                    continue
                if (line == ""):
                    continue
                products.append(json.loads(line))
    return products

def safe_run(func):
    """ Decorator to run a method wrapped in a try/except -> returns None upon exception """

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return None

    return func_wrapper


@safe_run
def get_name(api_data) -> str:
    """ Returns plain text; every product should have a name value """
    return api_data['name'].strip()


@safe_run
def get_brand(api_data) -> str:
    """ Returns plain text """
    brand = api_data['brand'].strip()
    if brand is None or brand == "":
        brand = "n/a"
    return brand


@safe_run
def get_description(api_data) -> str:
    """ Return the product description, often including HTML tags as well as plain text """
    return api_data['description'].strip()


@safe_run
# TODO
def get_all_image_urls(api_data) -> list:
    """ This will retrieve ALL of the image urls associated with the product; more than we need """
    return api_data['imageAssets']


@safe_run
# TODO
def get_large_image_urls(api_data):
    """ This is typically the image data we want to retrieve per product """
    images = [x['largeUrl'] for x in api_data['imageAssets']]
    return images


@safe_run
def get_package_size(api_data) -> str:
    return api_data['container_size'].strip()


@safe_run
def get_url(api_data) -> str:
    """ Returns the link to the product on the Loblaws domain; no guarantee the link is still accurate/active """
    return api_data['url'].strip()


def get_price(api_data) -> (int, str):
    """ Concatenates the price and unit values to produce something like '$6.99 ea' """
    price = api_data['price']
    m = re.search("([0-9]+\.*[0-9]*)", price)
    price_val = None
    if m:
        price_val = float(m.group(1))
    return price, price_val


@safe_run
def get_country_of_origin(api_data) -> str:
    return None


@safe_run
def get_ingredients(api_data) -> str:
    return api_data['ingredients'].strip()


@safe_run
def get_nutrition_facts(api_data):
    # All information is stored in nutritionFacts
    nutrition_facts = api_data['raw_nft']
    return nutrition_facts


@safe_run
def get_health_tips(api_data) -> str:
    return None


@safe_run
def get_safety_tips(api_data) -> str:
    return None


@safe_run
def get_breadcrumbs(api_data) -> list:
    """
    :return:    Returns list of of breadcrumbs in order from highest level to lowest level e.g.
                [Food, Fruits & Vegetables, Fruit, Apples]
    """
    breadcrumbs = api_data['breadcrumb'].split(" > ")
    return breadcrumbs


@safe_run
def get_upc_list(api_data) -> list:
    return []


@safe_run
def get_average_weight(api_data) -> str:
    return None


@safe_run
def get_nutrition_disclaimer(api_data) -> str:
    return None

# TODO
def load_images(image_dirs: list):
    for d in tqdm(image_dirs, desc="Loading images"):
        product_code = d.name
        try:
            # Grab most recent version of product
            product = Product.objects.filter(product_code=product_code).order_by('-created')[0]
        except:
            print(f'Could not find corresponding product in database for {product_code}')
            continue

        # Check if the product already has images associated with it
        existing_images = ProductImage.objects.filter(product__product_code=product_code)
        if len(existing_images) > 0:
            # print(f'Already have image records for {product}; skipping!')
            continue

        images = [x for x in list(d.glob('*')) if x.is_file()]
        product_image_paths = []
        for i in images:
            # Strip out MEDIA_ROOT for paths to behave properly with image field in ProductImage
            i = str(i).replace(settings.MEDIA_ROOT, "")
            try:
                product_image = ProductImage.objects.create(product=product,
                                                            image_path=i)
                product_image_paths.append(product_image.image_path.url)
            # Skip if the file path already exists
            except IntegrityError as e:
                pass


class Command(BaseCommand):
    help = 'Given an input product JSON directory (created by the Loblaws scraper), ' \
           'will load entries into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--input_dir', type=str, help='Path to input product JSON directory')
        parser.add_argument('--date', type=str,
                            help='Date in YYYY-MM-DD format. This should be the date that the scrape was executed.')
        parser.add_argument('--delete_products', action='store_true',
                            help='WARNING: Will delete all Loblaws products in the database!')

    def handle(self, *args, **options):
        if options['delete_products']:
            self.stdout.write(self.style.WARNING(f'Deleting all Loblaws products in the database...'))
            product_records = Product.objects.filter(store="LOBLAWS")
            product_records.delete()
            self.stdout.write(self.style.ERROR(f'Deleted all Loblaws records in the database!'))
            quit()

        # Product JSON
        infile_json = Path(options['input_dir']) / "out.json"
        scrape_date = parse_date(options['date'])

        self.stdout.write(self.style.SUCCESS(f'\nStarted loading Loblaws product JSON to database'))

        self.image_dir = Path(options['input_dir']) / 'images'
        self.load_loblaws(infile_json=infile_json, scrape_date=scrape_date)


    def load_loblaws(self, infile_json: str, scrape_date: str):

        CHANGE_REASON = 'New Loblaws Scrape Batch'
        json_data = read_json(infile_json)

        if len(json_data) < 1:
            self.stdout.write(self.style.ERROR(f'Could not find anything in your json file {infile_json}, quitting!'))
            quit()

        self.stdout.write(self.style.SUCCESS(f'Found {len(json_data)} products in {infile_json}'))


        # All product codes
        product_codes = set([f['item_number'] for f in json_data])
        # Total valid products scraped
        total_products = len(product_codes)

        # All Loblaws products in the DB
        existing_products = [x.product.product_code for x in LoblawsProduct.objects.all()]

        # Total number of products
        missing_products = len(list(set(existing_products) - set(product_codes)))
        new_products = len([x for x in product_codes if x not in existing_products])
        # Skip duplicates in the scrape data
        seen = set()

        # Create scrape batch
        scrape = ScrapeBatch.objects.create(
            missing_products=missing_products,
            new_products=new_products,
            total_products=total_products,
            scrape_date=scrape_date,
            store='LOBLAWS'
        )

        # Iterate over product json files
        existing_codes_dict = Product.generate_existing_product_codes_dict(store='LOBLAWS')
        for data in tqdm(json_data, desc="Uploading JSON"):
            if (data['name'] is None) | (data['name'] == ""):
                continue
            product_code = data['item_number']  # Files are named after product code
            # Skip duplicates in the scrape data
            if data['item_number'] in seen:
                continue

            # Get or create generic Product
            obj = Product.objects.create(product_code=product_code)
            obj.save()
            obj.changeReason = CHANGE_REASON

            # Get or create Loblaws Product
            product = LoblawsProduct.objects.create(product=obj)
            product.save()

            # Generic fields for Product model
            obj.store = 'LOBLAWS'

            # Normalize the apostrophes for name and brand
            obj.name = normalize_apostrophe(get_name(data))
            obj.brand = normalize_apostrophe(get_brand(data))

            price, price_float = get_price(data)
            obj.price, obj.price_float = price, price_float

            # UPC is no longer on loblaws website
            obj.upc_code = None  # Set the representative UPC code to the first entry in the list
            obj.upc_array = []

            obj.manufacturer = None  # Not sure if we have this
            obj.nielsen_product = None  # Can only be populated if we have a UPC
            obj.url = get_url(data)
            obj.scrape_date = timezone.now()
            obj.nutrition_available = None
            obj.breadcrumbs_array = get_breadcrumbs(data)
            obj.breadcrumbs_text = ",".join(get_breadcrumbs(data))
            obj.description = get_description(data)
            obj.batch = scrape

            # Get the images
            product_image_paths = []
            for i, img in enumerate(data['images']):
                if img['status'] != "downloaded":
                    continue

                # front, side, etc
                type = Path(img['url']).name.split("_")[1]

                path_use = str(self.image_dir / img['path']).replace(settings.MEDIA_ROOT, "")
                if len(ProductImage.objects.filter(image_path=path_use).all()) == 0:
                    product_image = ProductImage.objects.create(product = obj, image_path=path_use, image_number=i+1, image_label=type)
                    product_image.save()
                    product_image_paths.append(product_image.image_path.url)

            # Update most_recent flag of older duplicate products if necessary
            if product_code in existing_codes_dict.values():
                ids_to_demote = Product.test_if_most_recent(product_code=product_code,
                                                            existing_codes_dict=existing_codes_dict)
                Product.demote_most_recent_product_list(ids_to_demote)

            # Loblaws fields for LoblawsProduct model
            product.api_data = data
            nutrition_facts_raw = get_nutrition_facts(data)
            product.changeReason = CHANGE_REASON

            # Populate NutritionFacts model
            nutrition_facts, c = NutritionFacts.objects.get_or_create(product=obj)
            nutrition_facts.load_total_size(data)
            nutrition_facts.ingredients = get_ingredients(data)

            if nutrition_facts_raw is not None:
                nutrition_facts.load_scrapy_nutrition_facts(data,dv_in_val=True)
                obj.nutrition_available = True
            else:
                obj.nutrition_available = False

            if not c:
                nutrition_facts.changeReason = CHANGE_REASON

            # Commit to DB
            obj.save()
            product.save()
            nutrition_facts.save()

        self.stdout.write(self.style.SUCCESS(f'Done loading Loblaws-{str(scrape_date)} products to database!'))

        self.stdout.write(self.style.SUCCESS(f'Conducting category assignment step'))
        assign_categories()

        self.stdout.write(self.style.SUCCESS(f'Conducting variety pack assignment step'))
        assign_variety_pack_flag()

        self.stdout.write(self.style.SUCCESS(f'Calculating Atwater result for products'))
        calculate_atwater()

        self.stdout.write(self.style.SUCCESS(f'Loading complete!'))
