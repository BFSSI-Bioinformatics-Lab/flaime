import os
import django
import requests
import time


# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pathlib import Path
from datetime import datetime
from flaim.database.models import LoblawsProduct, ProductImage
from django.conf import settings

# Output directory should represent day script was run
OUTDIR = Path(settings.MEDIA_ROOT) / 'LOBLAWS' / datetime.today().strftime('%Y%m%d')


def get_image_urls_from_product(product: LoblawsProduct) -> [str]:
    images = product.get_large_image_urls()
    return images


def download_image(url: str, outfile: Path) -> bool:
    img_data = requests.get(url).content
    with open(str(outfile), 'wb') as handler:
        handler.write(img_data)
    if outfile.exists():
        return True
    return False


if __name__ == "__main__":
    products = LoblawsProduct.objects.filter(api_data__isnull=False)

    for p in products:
        # Check if we already have images in the DB
        images = ProductImage.objects.filter(product=p.product)
        if len(images) > 0:
            continue
        image_urls = get_image_urls_from_product(p)
        if image_urls is None:
            continue
        download_dir = OUTDIR / p.product.product_code
        download_dir.mkdir(exist_ok=True, parents=True)
        status = False

        for i in image_urls:
            outfile = download_dir / Path(i).name
            if outfile.exists():
                continue
            status = download_image(url=i, outfile=outfile)
        print(f'{status}\t{p.product.product_code}')
        time.sleep(1.5)

