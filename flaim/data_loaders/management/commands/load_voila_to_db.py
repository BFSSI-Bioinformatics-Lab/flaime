import json
from pathlib import Path
from django.conf import settings
from django.db import IntegrityError
from django.utils.dateparse import parse_date
from django.core.management.base import BaseCommand
from tqdm import tqdm

from flaim.database.models import Product, VoilaProduct, NutritionFacts, ProductImage, ScrapeBatch
from flaim.classifiers.management.commands.assign_categories import assign_categories
from flaim.data_loaders.management.commands.calculate_atwater import calculate_atwater
from django.contrib.auth import get_user_model

User = get_user_model()

# TODO: Implement automatic scanning/calling of this script upon finding new data

CHANGE_REASON = 'New Voila Scrape Batch'
EXPECTED_KEYS = {"product_code",
                 "product_name",
                 "website",
                 "created_date",
                 "UPC",
                 "SKU",
                 "url",
                 "breadcrumbs",
                 "Brand",
                 "size",
                 "price",
                 "long_desc",
                 "bullets",
                 "ingredients_txt",
                 "Lifestyle & Dietary Need",
                 "images",
                 "nft_present",
                 "nft_american",
                 "nielsen_product",
                 "nielsen_upc",
                 "nutrition"}


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


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


class Command(BaseCommand):
    help = 'Given an input Voila scrape directory (created by the Voila scraper), ' \
           'will load entries (including images) into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--input_dir', type=str, help='Path to input Voila directory')
        parser.add_argument('--date', type=str,
                            help='Date in YYYY-MM-DD format. This should be the date that the scrape was executed.')
        parser.add_argument('--delete_products', action='store_true',
                            help='WARNING: Will delete all Voila products in the database!')

    def handle(self, *args, **options):
        if options['delete_products']:
            self.stdout.write(self.style.WARNING(f'Deleting all Voila products in the database...'))
            product_records = Product.objects.filter(store="VOILA")
            product_records.delete()
            self.stdout.write(self.style.ERROR(f'Deleted all Voila records in the database!'))
            quit()

        scrape_date = parse_date(options['date'])

        # Read main json file
        f = list(Path(options['input_dir']).glob('*.json'))[0]
        assert f.exists()
        j = read_json(str(f))

        # Get image directory
        tmp = list(Path(options['input_dir']).glob('*'))
        image_dir = [x for x in tmp if x.is_dir()][0]
        assert image_dir.exists()

        self.stdout.write(self.style.SUCCESS(f'Started loading Voila products to database'))

        # Create scrape batch
        # All Voila products in the DB
        existing_products = [x.product.product_code for x in VoilaProduct.objects.all()]
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
            store='VOILA'
        )

        self.stdout.write(self.style.SUCCESS(f'Created new scrape batch for {scrape.scrape_date}'))

        # Iterate over all products
        existing_codes_dict = Product.generate_existing_product_codes_dict(store='VOILA')
        for p in tqdm(j, desc="Loading Voila JSON"):
            # Make sure all of the expected keys are populated at least with None.
            # Also rename the carbohydrate and carbohydrate_dv columns to match the DB
            for k in EXPECTED_KEYS:
                if k not in p:
                    p[k] = None

            product = Product.objects.create(product_code=p['product_code'])

            # Product fields
            product.name = normalize_apostrophe(p['product_name'])
            product.brand = normalize_apostrophe(p['Brand'])
            product.store = 'VOILA'

            # TODO: Make sure the UPC code is just the first entry
            if p['UPC'] is not None:
                first_upc_code = str(p['UPC']).split(',')[0]
                product.upc_code = first_upc_code
            product.url = p['url']

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
                product.price_units = "ea"  # TODO: This is just assumed because there is no value provided by the Voila scraper

            product.nutrition_available = p['nft_present']
            product.nielsen_product = p['nielsen_product']
            product.unidentified_nft_format = p['nft_american']
            product.batch = scrape

            # Update most_recent flag of older duplicate products if necessary
            if product.product_code in existing_codes_dict.values():
                ids_to_demote = Product.test_if_most_recent(product_code=product.product_code,
                                                            existing_codes_dict=existing_codes_dict)
                Product.demote_most_recent_product_list(ids_to_demote)

            # Change reason
            product.changeReason = CHANGE_REASON

            product.save()

            # Voila fields
            voila = VoilaProduct.objects.create(product=product)
            voila.nutrition_facts_json = p['nutrition']
            if len(p['images']['image_paths']) > 0:
                voila.image_directory = str(Path(p['images']['image_paths'][0]).parent)
            else:
                voila.image_directory = None
            voila.dietary_info = p['Lifestyle & Dietary Need']
            voila.bullets = p['bullets']
            voila.sku = p['SKU']
            voila.changeReason = CHANGE_REASON
            voila.save()

            # Nutrition fields
            # Pass over the nutrition dict to replace 'absent' with 0 and 'conflict' with None
            nutrition_dict = p['nutrition'].copy()

            # Correct carbohydrate values to proper name to ensure fields match with database
            if "carbohydrate" in nutrition_dict.keys():
                nutrition_dict['totalcarbohydrate'] = nutrition_dict['carbohydrate']
            if "carbohydrate_dv" in nutrition_dict.keys():
                nutrition_dict['totalcarbohydrate_dv'] = nutrition_dict['carbohydrate_dv']
            if "carbohydrate_unit" in nutrition_dict.keys():
                nutrition_dict['totalcarbohydrate_unit'] = nutrition_dict['carbohydrate_unit']

            for key, val in nutrition_dict.items():
                # Override bad values with 0 or None
                if val == 'absent':
                    nutrition_dict[key] = 0
                if val == 'conflict':
                    nutrition_dict[key] = None

                # Convert any 'o' values to numeric 0. This is an OCR error.
                if '_dv' in key and val is not None:
                    if type(val) == str and val.lower() == 'o':
                        nutrition_dict[key] = 0
                    elif type(val) == str:
                        nutrition_dict[key] = None
                    else:
                        nutrition_dict[key] = float(val)

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

            if p['size'] is not None:
                if len(p['size']) < 100:
                    nutrition.total_size = p['size']
                else:
                    nutrition.total_size = None

            if not c:
                nutrition.changeReason = CHANGE_REASON

            for key, val in nutrition_dict.items():
                if val is not None:
                    setattr(nutrition, key, val)

            # Serving size does not appear to be available in the Voila scrape data
            nutrition.serving_size_raw = None
            if 'serving_size' in nutrition_dict.keys() and 'serving_size_unit' in nutrition_dict.keys():
                nutrition.serving_size_raw = f'{nutrition_dict["serving_size"]} {nutrition_dict["serving_size_unit"]}'
            else:
                pass

            nutrition.serving_size = None
            if 'serving_size' in nutrition_dict.keys():
                nutrition.serving_size = nutrition_dict["serving_size"]

            nutrition.serving_size_units = None
            if 'serving_size_unit' in nutrition_dict.keys():
                nutrition.serving_size_units = nutrition_dict["serving_size_unit"]

            nutrition.save()

            # Images
            image_paths = p['images']['image_paths']
            image_labels = p['images']['image_labels']

            # Check if the product already has images associated with it
            existing_images = ProductImage.objects.filter(product__product_code=product.product_code)
            if len(existing_images) > 0:
                # print(f'Already have image records for {product}; skipping!')
                continue

            # Upload images if there are any
            if len(image_paths) > 0:
                for i, val in enumerate(image_paths):
                    # Note image_dir is the absolute path to the image directory
                    image_path = image_dir.parent / val
                    assert image_path.exists()
                    # Strip out media root so images behave correctly
                    image_path = str(image_path).replace(settings.MEDIA_ROOT, '')
                    try:
                        image = ProductImage.objects.create(product=product, image_path=image_path,
                                                            image_label=image_labels[i],
                                                            image_number=i)
                        image.save()
                    # Skip if the file path already exists
                    except IntegrityError as e:
                        pass
        self.stdout.write(self.style.SUCCESS(f'Done loading Voila-{str(scrape_date)} products to database!'))

        self.stdout.write(self.style.SUCCESS(f'Conducting category assignment step'))
        assign_categories()

        self.stdout.write(self.style.SUCCESS(f'Calculating Atwater result for products'))
        calculate_atwater()

        self.stdout.write(self.style.SUCCESS(f'Loading complete!'))
