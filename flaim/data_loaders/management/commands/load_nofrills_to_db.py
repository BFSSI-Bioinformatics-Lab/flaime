import json
from pathlib import Path
from django.conf import settings
from django.db import IntegrityError
from django.utils.dateparse import parse_date
from django.core.management.base import BaseCommand
from tqdm import tqdm

from flaim.data_loaders.management.accessories import assign_variety_pack_flag
from flaim.database.models import Product, NoFrillsProduct, NutritionFacts, ProductImage, ScrapeBatch
from flaim.classifiers.management.commands.assign_categories import assign_categories
from flaim.data_loaders.management.commands.calculate_atwater import calculate_atwater
from django.contrib.auth import get_user_model
from flaim.data_loaders.management.commands.load_loblaws_to_db import  read_json

User = get_user_model()

# TODO: Implement automatic scanning/calling of this script upon finding new data

CHANGE_REASON = 'New No Frills Scrape Batch'
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
    help = 'Given an input Grocery Gateway scrape directory (created by the Grocery Gateway scraper), ' \
           'will load entries (including images) into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--input_dir', type=str, help='Path to input Grocery Gateway directory')
        parser.add_argument('--date', type=str,
                            help='Date in YYYY-MM-DD format. This should be the date that the scrape was executed.')
        parser.add_argument('--delete_products', action='store_true',
                            help='WARNING: Will delete all Grocery Gateway products in the database!')

    def handle(self, *args, **options):
        if options['delete_products']:
            self.stdout.write(self.style.WARNING(f'Deleting all Grocery Gateway products in the database...'))
            product_records = Product.objects.filter(store="NOFRILLS")
            product_records.delete()
            self.stdout.write(self.style.ERROR(f'Deleted all Grocery Gateway records in the database!'))
            quit()


        infile_json = Path(options['input_dir']) / "out.json"
        scrape_date = parse_date(options['date'])

        self.image_dir = Path(options['input_dir']) / 'images'

        # Read main json file
        assert infile_json.exists()
        j = read_json(str(infile_json))

        self.stdout.write(self.style.SUCCESS(f'Started loading No Frills products to database'))

        # Create scrape batch
        # All Grocery Gateway products in the DB
        existing_products = [x.product.product_code for x in NoFrillsProduct.objects.all()]
        product_codes = set([x['item_number'] for x in j])
        missing_products = len(list(set(existing_products) - set(product_codes)))
        new_products = len([x for x in product_codes if x not in existing_products])
        total_products = len(product_codes)

        # TODO: If the script fails this will still be created, should probably clean up after itself
        scrape = ScrapeBatch.objects.create(
            missing_products=missing_products,
            new_products=new_products,
            total_products=total_products,
            scrape_date=scrape_date,
            store='NOFRILLS'
        )

        self.stdout.write(self.style.SUCCESS(f'Created new scrape batch for {scrape.scrape_date}'))
        # Skip duplicates in the scrape data
        seen = set()

        # Iterate over all products
        existing_codes_dict = Product.generate_existing_product_codes_dict(store='NOFRILLS')
        for p in tqdm(j, desc="Loading No Frills JSON"):
            # Make sure all of the expected keys are populated at least with None.
            # Also rename the carbohydrate and carbohydrate_dv columns to match the DB
            if (p['name'] is None) | (p['name'] == ""):
                continue
            # Skip duplicates in the scrape data
            if p['item_number'] in seen:
                continue
            seen.add(p['item_number'])

            product = Product.objects.create(product_code=p['item_number'])

            # Product fields
            product.name = normalize_apostrophe(p['name'])
            product.store = 'NOFRILLS'

            product.upc_code = p['barcode']
            product.url = p['url']

            product.description = p['description']
            if p['breadcrumb'] is not None:
                product.breadcrumbs_text = p['breadcrumb'].strip()
                product.breadcrumbs_array = [x.strip() for x in p['breadcrumb'].strip().split('|')]

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
                product.price_units = "ea"  # TODO: This is just assumed because there is no value provided by the Grocery Gateway scraper


            nft_raw = p['raw_nft']
            product.nutrition_available = True
            if nft_raw == "":
                product.nutrition_available = False
            product.batch = scrape

            # Update most_recent flag of older duplicate products if necessary
            if product.product_code in existing_codes_dict.values():
                ids_to_demote = Product.test_if_most_recent(product_code=product.product_code,
                                                            existing_codes_dict=existing_codes_dict)
                Product.demote_most_recent_product_list(ids_to_demote)

            # Change reason
            product.changeReason = CHANGE_REASON

            product.save()

            nutrition_facts, c = NutritionFacts.objects.get_or_create(product=product)
            nutrition_facts.load_total_size(p)
            nutrition_facts.ingredients = p['ingredients']
            nutrition_facts.load_scrapy_nutrition_facts(p, dv_in_val=True)
            nutrition_facts.save()

            # Get the images
            product_image_paths = []
            for i, img in enumerate(p['images']):
                if img['status'] != "downloaded":
                    continue

                path_use = str(self.image_dir / img['path']).replace(settings.MEDIA_ROOT, "")
                if ProductImage.objects.filter(image_path=path_use).first() is not None:
                    continue
                product_image = ProductImage.objects.create(product = product, image_path=path_use, image_number=i+1)
                product_image.save()
                product_image_paths.append(product_image.image_path.url)

            nf = NoFrillsProduct.objects.create(product=product)
            nf.save()

        self.stdout.write(
            self.style.SUCCESS(f'Done loading No Frills - {str(scrape_date)} products to database!'))

        self.stdout.write(self.style.SUCCESS(f'Conducting category assignment step'))
        assign_categories()

        self.stdout.write(self.style.SUCCESS(f'Conducting variety pack assignment step'))
        assign_variety_pack_flag()

        self.stdout.write(self.style.SUCCESS(f'Calculating Atwater result for products'))
        calculate_atwater()

        self.stdout.write(self.style.SUCCESS(f'Loading complete!'))
