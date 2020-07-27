import json
from pathlib import Path
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from flaim.database.models import Product, LoblawsProduct, NutritionFacts, ScrapeBatch, ProductImage
from tqdm import tqdm


# TODO: Implement automatic scanning/calling of this script upon finding new data

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


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
    if brand is None or brand is "":
        brand = "n/a"
    return brand


@safe_run
def get_description(api_data) -> str:
    """ Return the product description, often including HTML tags as well as plain text """
    return api_data['description'].strip()


@safe_run
def get_all_image_urls(api_data) -> list:
    """ This will retrieve ALL of the image urls associated with the product; more than we need """
    return api_data['imageAssets']


@safe_run
def get_large_image_urls(api_data):
    """ This is typically the image data we want to retrieve per product """
    images = [x['largeUrl'] for x in api_data['imageAssets']]
    return images


@safe_run
def get_package_size(api_data) -> str:
    return api_data['packageSize'].strip()


@safe_run
def get_url(api_data) -> str:
    """ Returns the link to the product on the Loblaws domain; no guarantee the link is still accurate/active """
    return 'https://www.loblaws.ca' + api_data['link'].strip()


def get_price(api_data) -> (int, str):
    """ Concatenates the price and unit values to produce something like '$6.99 ea' """
    try:
        price, unit = float(api_data['prices']['price']['value']), api_data['prices']['price']['unit']
    except (TypeError, KeyError) as e:
        print(f'Could not retrieve price for product')
        price, unit = None, None
    return price, unit


@safe_run
def get_country_of_origin(api_data) -> str:
    return api_data['countryOfOrigin'].strip()


@safe_run
def get_ingredients(api_data) -> str:
    return api_data['ingredients'].strip()


@safe_run
def get_nutrition_facts(api_data):
    # All information is stored in nutritionFacts
    nutrition_facts = api_data['nutritionFacts']

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
def get_health_tips(api_data) -> str:
    return api_data['healthTips'].strip()


@safe_run
def get_safety_tips(api_data) -> str:
    return api_data['safetyTips'].strip()


@safe_run
def get_breadcrumbs(api_data) -> list:
    """
    :return:    Returns list of of breadcrumbs in order from highest level to lowest level e.g.
                [Food, Fruits & Vegetables, Fruit, Apples]
    """
    breadcrumbs = api_data['breadcrumbs']
    breadcrumb_names = [x['name'].strip() for x in breadcrumbs]
    return breadcrumb_names


@safe_run
def get_upc_list(api_data) -> list:
    return [x.strip() for x in api_data['upcs']]


@safe_run
def get_average_weight(api_data) -> str:
    return api_data['averageWeight'].strip()


@safe_run
def get_nutrition_disclaimer(api_data) -> str:
    return api_data['productNutritionDisclaimer'].strip()


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
        product_json_dir = Path(options['input_dir']) / 'product_json'
        scrape_date = parse_date(options['date'])

        self.stdout.write(self.style.SUCCESS(f'\nStarted loading Loblaws product JSON to database'))

        self.load_loblaws(product_json_dir=product_json_dir, scrape_date=scrape_date)

        # Images
        self.stdout.write(self.style.SUCCESS(f'\nStarted loading Loblaws images to database'))
        input_dir = Path(options['input_dir']) / 'product_images'
        image_dirs = input_dir.glob("*")
        image_dirs = [x for x in image_dirs if x.is_dir()]
        load_images(image_dirs)
        self.stdout.write(self.style.SUCCESS(f'\nDone loading Loblaws images to database!'))

    def load_loblaws(self, product_json_dir: Path, scrape_date: str):

        CHANGE_REASON = 'New Loblaws Scrape Batch'
        json_files = list(product_json_dir.glob("*.json"))

        if len(json_files) < 1:
            self.stdout.write(self.style.ERROR(f'Could not find any JSON files in {product_json_dir}, quitting!'))
            quit()

        self.stdout.write(self.style.SUCCESS(f'Found {len(json_files)} JSON files in {product_json_dir}'))

        # TODO: I think some of the following logic (before loading individual json files) is super slow
        # Total valid products scraped
        filtered_json_files = [f for f in json_files if f.stat().st_size > 1000]
        total_products = len(filtered_json_files)

        # All product codes
        product_codes = [f.with_suffix("").name for f in filtered_json_files]

        # All Loblaws products in the DB
        existing_products = [x.product.product_code for x in LoblawsProduct.objects.all()]

        # Total number of products
        missing_products = len(list(set(existing_products) - set(product_codes)))
        new_products = len([x for x in product_codes if x not in existing_products])

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
        for j in tqdm(filtered_json_files, desc="Uploading JSON"):
            product_code = j.with_suffix("").name  # Files are named after product code

            try:
                data = read_json(j)
            except json.decoder.JSONDecodeError as e:
                # self.stdout.write(self.style.ERROR(f'Skipping product JSON {j} due to exception:\n{e}'))
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
            obj.name = get_name(data)

            price_float, price_units = get_price(data)
            obj.price_float, obj.price_units = price_float, price_units
            obj.price = f'${price_float} {price_units}'
            obj.brand = get_brand(data)

            upc_list = get_upc_list(data)
            if upc_list is not None:
                obj.upc_code = upc_list[0]  # Set the representative UPC code to the first entry in the list

            obj.manufacturer = None  # Not sure if we have this
            obj.nielsen_product = None  # TODO: Probably populate this post-hoc. Ask Adrian about this.
            obj.url = get_url(data)
            obj.scrape_date = timezone.now()
            obj.nutrition_available = None
            obj.breadcrumbs_array = get_breadcrumbs(data)
            obj.breadcrumbs_text = ",".join(get_breadcrumbs(data))
            obj.description = get_description(data)
            obj.batch = scrape

            # Update most_recent flag of older duplicate products if necessary
            if product_code in existing_codes_dict.values():
                ids_to_demote = Product.test_if_most_recent(product_code=product_code,
                                                            existing_codes_dict=existing_codes_dict)
                Product.demote_most_recent_product_list(ids_to_demote)

            # Loblaws fields for LoblawsProduct model
            product.api_data = data
            nutrition_facts_json = get_nutrition_facts(data)
            product.changeReason = CHANGE_REASON

            # Populate NutritionFacts model
            nutrition_facts, c = NutritionFacts.objects.get_or_create(product=obj)
            nutrition_facts.load_total_size(data)
            nutrition_facts.ingredients = get_ingredients(data)

            if nutrition_facts_json is not None:
                nutrition_facts.load_loblaws_nutrition_facts_json(nutrition_facts_json)
                obj.nutrition_available = True
            else:
                obj.nutrition_available = False

            if not c:
                nutrition_facts.changeReason = CHANGE_REASON

            # Commit to DB
            obj.save()
            product.save()
            nutrition_facts.save()

            # if created_:
            #     self.stdout.write(self.style.SUCCESS(f'SAVED {product}'))
            # else:
            #     self.stdout.write(self.style.SUCCESS(f'UPDATED {product}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone loading Loblaws-{str(scrape_date)} products to database!'))
