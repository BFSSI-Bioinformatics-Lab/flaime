import os
import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pathlib import Path
from flaim.database.models import ProductImage, Product, LoblawsProduct
from django.conf import settings
from django.db import IntegrityError

if __name__ == "__main__":
    image_dirs = list(Path("/home/forest/PycharmProjects/flaim/flaim/media/LOBLAWS/20200206").glob('*'))
    for d in image_dirs:
        product_code = d.name
        try:
            product = Product.objects.get(product_code=product_code)
        except:
            continue
        loblaws_product = LoblawsProduct.objects.get(product__product_code=product_code)

        # Update image directory
        if loblaws_product.image_directory is None:
            loblaws_product.image_directory = str(d)
            loblaws_product.save()

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
