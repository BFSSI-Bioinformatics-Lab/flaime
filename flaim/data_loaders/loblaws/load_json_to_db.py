import os
import json
from pathlib import Path
from django.conf import settings
from django.utils import timezone
import pytz
import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import Product, LoblawsProduct, NutritionFacts, ScrapeBatch

# TODO: Put this stuff somewhere more permanent, like the media dir?
DATADIR = Path('/home/forest/Documents/FLAIME/loblaws_data/product_data_03042020')

# For Django historical model
CHANGE_REASON = 'New Loblaws Scrape Batch'


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
    return api_data['brand'].strip()


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


if __name__ == "__main__":
    json_files = list(DATADIR.glob("*.json"))

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
    )

    for j in filtered_json_files:
        product_code = j.with_suffix("").name  # Files are named after product code

        try:
            data = read_json(j)
        except json.decoder.JSONDecodeError as e:
            print(f'Skipping product JSON {j} due to exception:\n{e}')
            continue

        # Get or create generic Product
        obj, created = Product.objects.get_or_create(product_code=product_code)
        if created:
            obj.save()
        else:
            obj.changeReason = CHANGE_REASON

        # Get or create Loblaws Product
        product, created_ = LoblawsProduct.objects.get_or_create(product=obj)
        if created_:
            product.save()

        # Generic fields for Product model
        obj.store = 'LOBLAWS'
        obj.name = get_name(data)
        obj.price_float, obj.price_units = get_price(data)
        obj.brand = get_brand(data)

        upc_list = get_upc_list(data)
        if upc_list is not None:
            obj.upc_code = upc_list[0]  # Set the representative UPC code to the first entry in the list

        obj.manufacturer = None  # Not sure if we have this
        obj.nielsen_product = None  # Might need to be populated posthoc
        obj.url = get_url(data)
        obj.scrape_date = timezone.now()
        obj.nutrition_available = None  # Figure out how to populate this

        # Loblaws fields for LoblawsProduct model
        product.api_data = data
        product.breadcrumbs_array = get_breadcrumbs(data)
        product.breadcrumbs_text = ",".join(get_breadcrumbs(data))
        product.description = get_description(data)

        nutrition_facts_json = get_nutrition_facts(data)
        product.nutrition_facts_json = nutrition_facts_json  # this is the source for NFT

        if not created_:
            product.changeReason = CHANGE_REASON

        # Populate NutritionFacts model
        nutrition_facts, c = NutritionFacts.objects.get_or_create(product=obj)
        nutrition_facts.load_total_size(data)
        nutrition_facts.ingredients = get_ingredients(data)

        if nutrition_facts_json is not None:
            nutrition_facts.load_loblaws_nutrition_facts_json(nutrition_facts_json)

        if not c:
            nutrition_facts.changeReason = CHANGE_REASON

        # Commit to DB
        obj.save()
        product.save()
        nutrition_facts.save()

        if created_:
            print(f'Successfully SAVED {product} to database')
        else:
            print(f'Successfully UPDATED {product}')
