import os
import json
import django
import requests
import time

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pathlib import Path
from flaim.database.models import LoblawsProduct, ProductImage, ScrapeBatch
from django.conf import settings

# Output directory should represent day scrape was collected
SCRAPE_DATE = '2020-04-17'
OUTDIR = Path(settings.MEDIA_ROOT) / 'LOBLAWS' / SCRAPE_DATE
DATADIR = Path(f"/home/forest/Documents/FLAIME/loblaws_data/product_data_{SCRAPE_DATE}")  # Product data


def safe_run(func):
    """ Decorator to run a method wrapped in a try/except -> returns None upon exception """

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return None

    return func_wrapper


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


@safe_run
def get_large_image_urls(api_data):
    """ This is typically the image data we want to retrieve per product """
    images = [x['largeUrl'] for x in api_data['imageAssets']]
    return images


def download_image(url: str, outfile: Path) -> bool:
    img_data = requests.get(url).content
    with open(str(outfile), 'wb') as handler:
        handler.write(img_data)
    if outfile.exists():
        return True
    print(f'URL {url} failed')
    return False


def download_all_images():
    json_files = list(DATADIR.glob("*.json"))
    for j in json_files:
        print(f'Retrieving images for {j.name}')
        try:
            data = read_json(j)
        except json.decoder.JSONDecodeError as e:
            print(f'Skipping product JSON {j} due to exception:\n{e}')
            continue

        try:
            p = LoblawsProduct.objects.get(product__product_code=str(j.with_suffix("").name))
        except LoblawsProduct.DoesNotExist as e:
            print(f'Corresponding database object does not exist for {j.with_suffix("").name}')
            continue

        image_urls = get_large_image_urls(data)
        if image_urls is None:
            print(f'No images for {p} found')
            continue

        download_dir = OUTDIR / p.product.product_code
        download_dir.mkdir(exist_ok=True, parents=True)

        status = False
        for i in image_urls:
            if type(i) != str:
                continue
            outfile = download_dir / Path(i).name
            if outfile.exists():
                print(f'Skipping {outfile.name}')
                continue
            status = download_image(url=i, outfile=outfile)
            print(f'Retrieved {outfile.name}: {status}')
        time.sleep(1.5)


if __name__ == "__main__":
    download_all_images()
