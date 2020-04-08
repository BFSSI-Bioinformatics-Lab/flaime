import os
import json
from pathlib import Path
from django.conf import settings
from django.db import IntegrityError

import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import Product, WalmartProduct, NutritionFacts, ProductImage

# For Django historical model
CHANGE_REASON = 'New Walmart Scrape Batch'


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


if __name__ == "__main__":
    f = Path("/home/forest/Documents/FLAIME/walmart_data/subset_test.json")
    image_dir = Path("/home/forest/PycharmProjects/flaim/flaim/media/WALMART/")
    j = read_json(str(f))

    # Create scrape batch
    Product.objects.filter(store='WALMART').delete()

    for p in j:
        product, created = Product.objects.get_or_create(product_code=p['product_code'])

        # Product fields
        product.name = p['product_name']
        product.store = 'WALMART'
        product.upc_code = p['UPC']
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
        nutrition.total_size = p['size']
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
