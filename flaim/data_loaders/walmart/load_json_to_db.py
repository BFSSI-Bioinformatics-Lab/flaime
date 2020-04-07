import os
import json
from pathlib import Path
from django.conf import settings

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
    f = Path("/home/forest/Documents/FLAIME/walmart_data/2020-03_update.json")
    j = read_json(str(f))

    for p in j:
        product, created = Product.objects.get_or_create(product_code=p['product_code'])
        product.save()

        # Product fields
        product.name = p['product_name']
        product.store = 'WALMART',
        product.scrape_date = p['created_date'],
        product.upc_code = p['UPC'],
        product.url = p['url'],
        product.brand = p['Brand']
        product.price = p['price']
        product.nutrition_available = p['nft_present']
        product.nielsen_product = p['nielsen_product']
        product.save()

        if not created:
            product.changeReason = CHANGE_REASON

        print(product)

        # Walmart fields
        walmart, created_ = WalmartProduct.objects.get_or_create(product=product)
        walmart.save()
        walmart.nutrition_facts_json = p['nutrition']
        walmart.description = p['long_desc']
        walmart.dietary_info = p['Lifestyle & Dietary Need']
        walmart.bullets = p['bullets']
        walmart.breadcrumbs_text = p['breadcrumbs'].strip()
        walmart.breadcrumbs_array = [x.strip() for x in p['breadcrumbs'].strip().split('>')]

        if not created_:
            walmart.changeReason = CHANGE_REASON

        # Nutrition fields
        nutrition, c = NutritionFacts.objects.get_or_create(product=product)
        nutrition.save()
        nutrition.ingredients = p[' ingredients_txt']  # TODO: Remove the space once Adrian removes it on his end
        nutrition.size = p['size']

        if not c:
            nutrition.changeReason = CHANGE_REASON

        for key, val in p['nutrition'].items():
            if val is not None:
                setattr(nutrition, key, val)
        nutrition.save()

        # Cleanup
        product.delete()
        walmart.delete()
        nutrition.delete()
        break
