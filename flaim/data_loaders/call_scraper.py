import os
import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pathlib import Path
from django.conf import settings
from flaim.data_loaders.loblaws_scraper import run_loblaws_scraper


def enqueue_loblaws_scraper(url: str, outdir: Path, filter_keyword: str):
    """ Submits a Loblaws scraping job to RQ """
    loblaws_result = run_loblaws_scraper(url=url, outdir=outdir, filter_keyword=filter_keyword).delay()


if __name__ == "__main__":
    loblaws_outdir = Path(settings.MEDIA_ROOT)
    enqueue_loblaws_scraper(url='https://www.loblaws.ca/Food/Pantry/Breakfast/c/LSL001008004000?navid=Breakfast',
                            outdir=loblaws_outdir,
                            filter_keyword='CEREAL')
