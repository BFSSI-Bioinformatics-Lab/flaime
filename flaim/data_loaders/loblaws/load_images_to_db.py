import os
from pathlib import Path
from django.conf import settings
from django.utils.dateparse import parse_date
from django.db import IntegrityError

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import Product, ProductImage

SCRAPE_DATE = parse_date('2020-04-17')  # YYYY-MM-DD
IMAGE_DIRS = list(Path(f"/home/forest/PycharmProjects/flaim/flaim/media/LOBLAWS/{str(SCRAPE_DATE)}").glob('*'))


def load_images(image_dirs: list):
    for d in image_dirs:
        product_code = d.name
        try:
            product = Product.objects.get(product_code=product_code)
        except:
            continue

        # Strip out MEDIA_ROOT for paths to behave properly with image field in ProductImage
        images = [str(x).replace(settings.MEDIA_ROOT + "/", "") for x in list(d.glob('*')) if x.is_file()]
        for i in images:
            try:
                ProductImage.objects.create(product=product,
                                            image_path=i)
            # Skip if the file path already exists
            except IntegrityError as e:
                pass

        print(f'Done with {product_code}')


if __name__ == "__main__":
    load_images(IMAGE_DIRS)
