from pathlib import Path
from django.conf import settings
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from flaim.database.models import Product, ProductImage


def load_images(image_dirs: list):
    for d in image_dirs:
        product_code = d.name
        try:
            product = Product.objects.get(product_code=product_code)
        except:
            print(f'Could not find corresponding product in database for {product_code}')
            continue

        # Check if the product already has images associated with it
        existing_images = ProductImage.objects.filter(product=product)
        if len(existing_images) > 0:
            print(f'Already have image records for {product}; skipping!')
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


class Command(BaseCommand):
    help = 'Given an input product image directory (created by the Loblaws scraper), ' \
           'will load entries into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--input_dir', type=str, help='Path to input product image directory')

    def handle(self, *args, **options):
        input_dir = Path(options['input_dir'])
        image_dirs = input_dir.glob("*")
        image_dirs = [x for x in image_dirs if x.is_dir()]
        load_images(image_dirs)
        self.stdout.write(self.style.SUCCESS(f'\nDone loading Loblaws images to database!'))
