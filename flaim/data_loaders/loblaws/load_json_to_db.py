import os
import json
from pathlib import Path
from django.conf import settings

import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import Product, LoblawsProduct

# TODO: Put this stuff somewhere more permanent, like the media dir?
DATADIR = Path('/home/forest/loblaws_api/product_data_04022020')


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


def populate_api_data(product_json: Path) -> bool:
    """
    Takes a product JSON file retrieved with product_detail_api.py and populates the relevant
    Product/LoblawsProduct model
    :param product_json: Path to product JSON file
    :return: True if JSON field populated, else False
    """
    product_code = product_json.with_suffix("").name
    obj, created = Product.objects.get_or_create(product_code=product_code)
    if created:
        obj.save()
        data = read_json(product_json)
        obj_, created_ = LoblawsProduct.objects.get_or_create(product=obj)
        obj_.api_data = data
        obj_.save()
        obj_.json_to_fields()
        print(f'Created record for {product_code}')
    else:
        print(f"JSON data already exists for {product_code}")
    return created


if __name__ == "__main__":
    json_files = list(DATADIR.glob("*.json"))
    for j in json_files:
        populate_api_data(j)

    # Price updates
    for x in LoblawsProduct.objects.all():
        if x.api_data:
            x.product.price_value, x.product.price_units = x.get_price()
            x.product.save()

    # Breadcrumbs updates
    for x in LoblawsProduct.objects.all():
        breadcrumbs = x.get_breadcrumbs()
        x.breadcrumbs_array = breadcrumbs
        x.breadcrumbs_text = ",".join(breadcrumbs)
        x.save()

