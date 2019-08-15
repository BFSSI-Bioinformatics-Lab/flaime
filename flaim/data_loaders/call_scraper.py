from pathlib import Path
from django.conf import settings
from flaim.data_loaders.loblaws_scraper import run_loblaws_scraper


def enqueue_loblaws_scraper(url: str, outdir: Path, filter_keyword: str):
    """ Submits a Loblaws scraping job to RQ """
    loblaws_result = run_loblaws_scraper(url=url, outdir=outdir, filter_keyword=filter_keyword).delay()


if __name__ == "__main__":

    loblaws_outdir = Path(settings.MEDIA_ROOT) / 'LOBLAWS_PRODUCTS'
    loblaws_outdir.mkdir(exist_ok=True, parents=True)
    enqueue_loblaws_scraper(url='https://www.loblaws.ca/Food/Pantry/Breakfast/c/LSL001008004000?navid=Breakfast',
                            outdir=loblaws_outdir,
                            filter_keyword='CEREAL')
