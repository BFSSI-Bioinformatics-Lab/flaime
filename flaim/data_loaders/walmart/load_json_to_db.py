import os
import json
import django
from pathlib import Path
from django.conf import settings
from django.db import IntegrityError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import Product, WalmartProduct, NutritionFacts, ProductImage, ScrapeBatch

CHANGE_REASON = 'New Walmart Scrape Batch'
POTENTIAL_KEYS = {'ingredients_txt', 'url', 'nutrition', 'SKU', 'created_date', 'nielsen_product', 'product_code',
                  'breadcrumbs', 'bullets', 'size', 'nft_american', 'website', 'images', 'product_name', 'UPC', 'Brand',
                  'nft_present', 'nielsen_upc', 'price', 'long_desc', 'Lifestyle & Dietary Need'}


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


if __name__ == "__main__":
    f = Path("/home/forest/Documents/FLAIME/walmart_data/2020-04-07.json")
    image_dir = Path("/home/forest/PycharmProjects/flaim/flaim/media/WALMART/")
    j = read_json(str(f))

    # Cleanup
    Product.objects.filter(store='WALMART').delete()

    # Create scrape batch
    # All Walmart products in the DB
    existing_products = [x.product.product_code for x in WalmartProduct.objects.all()]
    product_codes = [x['product_code'] for x in j]
    missing_products = len(list(set(existing_products) - set(product_codes)))
    new_products = len([x for x in product_codes if x not in existing_products])
    total_products = len(j)

    scrape = ScrapeBatch.objects.create(
        missing_products=missing_products,
        new_products=new_products,
        total_products=total_products,
    )

    for p in j:

        # Make sure all of the expected keys are populated at least with None.
        for k in POTENTIAL_KEYS:
            if k not in p:
                p[k] = None

        product, created = Product.objects.get_or_create(product_code=p['product_code'])

        # Product fields
        product.name = p['product_name']
        product.store = 'WALMART'

        # TODO: Make sure the UPC code is just the first entry
        first_upc_code = p['UPC'].split(',')[0]
        product.upc_code = first_upc_code
        product.url = p['url']

        product.brand = p['Brand']

        if p['price'] == 'price unavailable':
            product.price = None
        else:
            product.price = p['price']
        product.nutrition_available = p['nft_present']
        product.nielsen_product = p['nielsen_product']
        product.nft_american = p['nft_american']

        if not created:
            product.changeReason = CHANGE_REASON

        product.save()

        print(product)

        # Walmart fields
        walmart, created_ = WalmartProduct.objects.get_or_create(product=product)
        walmart.nutrition_facts_json = p['nutrition']
        walmart.image_directory = str(Path(p['images']['image_paths'][0]).parent)  # TODO: This is bad
        walmart.description = p['long_desc']
        walmart.dietary_info = p['Lifestyle & Dietary Need']
        walmart.bullets = p['bullets']
        walmart.sku = p['SKU']
        walmart.breadcrumbs_text = p['breadcrumbs'].strip()
        walmart.breadcrumbs_array = [x.strip() for x in p['breadcrumbs'].strip().split('>')]
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
        nutrition.save()

        # Images
        image_paths = p['images']['image_paths']
        image_labels = p['images']['image_labels']

        for i, val in enumerate(image_paths):
            image_path = str(image_dir / val).replace(settings.MEDIA_ROOT + "/", "")
            try:
                image = ProductImage.objects.create(product=product, image_path=image_path, image_label=image_labels[i],
                                                    image_number=i)
                image.save()
            # Skip if the file path already exists
            except IntegrityError as e:
                pass
