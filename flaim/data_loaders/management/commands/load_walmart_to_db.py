import json
from pathlib import Path
from django.conf import settings
from django.db import IntegrityError
from django.utils.dateparse import parse_date
from django.core.management.base import BaseCommand
from flaim.database.models import Product, WalmartProduct, NutritionFacts, ProductImage, ScrapeBatch

# TODO: Implement automatic scanning/calling of this script upon finding new data
# TODO: Ask Adrian not to .tar.gz the image directory so I can access it directly

CHANGE_REASON = 'New Walmart Scrape Batch'
EXPECTED_KEYS = {'ingredients_txt', 'url', 'nutrition', 'SKU', 'created_date', 'nielsen_product', 'product_code',
                 'breadcrumbs', 'bullets', 'size', 'nft_american', 'website', 'images', 'product_name', 'UPC', 'Brand',
                 'nft_present', 'nielsen_upc', 'price', 'long_desc', 'Lifestyle & Dietary Need'}


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


class Command(BaseCommand):
    help = 'Given an input Walmart scrape directory (created by the Walmart scraper), ' \
           'will load entries (including images) into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--input_dir', type=str, help='Path to input Walmart directory')
        parser.add_argument('--date', type=str,
                            help='Date in YYYY-MM-DD format. This should be the date that the scrape was executed.')

    def handle(self, *args, **options):
        scrape_date = parse_date(options['date'])

        # Read main json file
        f = list(Path(options['input_dir']).glob('*.json'))[0]
        assert f.exists()
        j = read_json(str(f))

        # Get image directory
        tmp = list(Path(options['input_dir']).glob('*'))
        image_dir = [x for x in tmp if x.is_dir()][0]
        assert image_dir.exists()

        # Cleanup
        Product.objects.filter(store='WALMART').delete()

        # Create scrape batch
        # All Walmart products in the DB
        existing_products = [x.product.product_code for x in WalmartProduct.objects.all()]
        product_codes = [x['product_code'] for x in j]
        missing_products = len(list(set(existing_products) - set(product_codes)))
        new_products = len([x for x in product_codes if x not in existing_products])
        total_products = len(j)

        # TODO: If the script fails this will still be created, should probably clean up after itself
        scrape = ScrapeBatch.objects.create(
            missing_products=missing_products,
            new_products=new_products,
            total_products=total_products,
            scrape_date=scrape_date,
            store='WALMART'
        )

        # Iterate over all products
        for p in j:
            # Make sure all of the expected keys are populated at least with None.
            # Also rename the carbohydrate and carbohydrate_dv columns to match the DB
            for k in EXPECTED_KEYS:
                if k not in p:
                    p[k] = None
                if k == 'carbohydrate':
                    p['totalcarbohydrate'] = p.pop('carbohydrate')
                if k == 'carbohydrate_dv':
                    p['totalcarbohydrate_dv'] = p.pop('carbohydrate_dv')

            product, created = Product.objects.get_or_create(product_code=p['product_code'])

            # Product fields
            product.name = p['product_name']
            product.store = 'WALMART'

            # TODO: Make sure the UPC code is just the first entry

            if p['UPC'] is not None:
                first_upc_code = str(p['UPC']).split(',')[0]
                product.upc_code = first_upc_code
            product.url = p['url']
            product.brand = p['Brand']
            product.description = p['long_desc']
            if p['breadcrumbs'] is not None:
                product.breadcrumbs_text = p['breadcrumbs'].strip()
                product.breadcrumbs_array = [x.strip() for x in p['breadcrumbs'].strip().split('>')]

            if p['price'] == 'price unavailable':
                product.price = 'price unavailable'
            elif p['price'] is not None:
                if '¢' in p['price']:
                    product.price_float = float(p['price'].replace('¢', '')) / 100
                elif '\u00a2' in p['price']:  # Weird character that represents cents
                    product.price_float = float(p['price'].replace('\u00a2', '')) / 100
                elif '$' in p['price']:
                    product.price_float = float(p['price'].replace('$', ''))
                product.price = p['price']
                product.price_units = "ea"  # TODO: This is just assumed because there is no value provided by the Walmart scraper

            product.nutrition_available = p['nft_present']
            product.nielsen_product = p['nielsen_product']
            product.unidentified_nft_format = p['nft_american']
            product.batch = scrape

            if not created:
                product.changeReason = CHANGE_REASON

            product.save()

            print(product)

            # Walmart fields
            walmart, created_ = WalmartProduct.objects.get_or_create(product=product)
            walmart.nutrition_facts_json = p['nutrition']
            if len(p['images']['image_paths']) > 0:
                walmart.image_directory = str(Path(p['images']['image_paths'][0]).parent)
            else:
                walmart.image_directory = None
            walmart.dietary_info = p['Lifestyle & Dietary Need']
            walmart.bullets = p['bullets']
            walmart.sku = p['SKU']
            if not created_:
                walmart.changeReason = CHANGE_REASON
            walmart.save()

            # Nutrition fields
            # Pass over the nutrition dict to replace 'absent' with 0 and 'conflict' with None
            nutrition_dict = p['nutrition'].copy()
            for key, val in nutrition_dict.items():
                if val == 'absent':
                    nutrition_dict[key] = 0
                if val == 'conflict':
                    nutrition_dict[key] = None
                # TODO: This is a hack to convert any 'o' values to numeric 0. This is an OCR error.
                if '_dv' in key and val is not None:
                    if type(val) == str and val.lower() == 'o':
                        nutrition_dict[key] = 0
                    elif type(val) == str:
                        nutrition_dict[key] = None

            # Need to iterate through the nutrition dict and convert mg to grams, and dv/100
            for key, val in nutrition_dict.items():
                if '_unit' in key and val is not None:
                    if str(val).lower() == 'mg':
                        nutrient_to_adjust = key.replace('_unit', '')
                        if nutrition_dict[nutrient_to_adjust] is None:
                            continue
                        nutrition_dict[nutrient_to_adjust] = nutrition_dict[nutrient_to_adjust] / 1000
                if '_dv' in key and val is not None:
                    nutrition_dict[key] = val / 100

            nutrition, c = NutritionFacts.objects.get_or_create(product=product)
            nutrition.ingredients = p['ingredients_txt']

            # TODO: There's a bug where the size value can just be a crazy string. Here's a temporary hack to get around it.
            if p['size'] is not None:
                if len(p['size']) < 100:
                    nutrition.total_size = p['size']
                else:
                    nutrition.total_size = None

            if not c:
                nutrition.changeReason = CHANGE_REASON

            # TODO: Verify Adrian's keys correspond with mine
            for key, val in nutrition_dict.items():
                if val is not None:
                    setattr(nutrition, key, val)

            # Serving size is weird
            nutrition.serving_size_raw = f'{p["serving_size"]} {p["serving_size_unit"]}'
            nutrition.serving_size = p["serving_size"]
            nutrition.serving_size_units = p["serving_size_unit"]

            nutrition.save()

            # Images
            image_paths = p['images']['image_paths']
            image_labels = p['images']['image_labels']

            if len(image_paths) > 0:
                for i, val in enumerate(image_paths):
                    image_path = str(image_dir / val).replace(settings.MEDIA_ROOT, "")
                    try:
                        image = ProductImage.objects.create(product=product, image_path=image_path,
                                                            image_label=image_labels[i],
                                                            image_number=i)
                        image.save()
                    # Skip if the file path already exists
                    except IntegrityError as e:
                        pass
        print(f'\nDone loading Walmart-{str(scrape_date)} products to database!')
