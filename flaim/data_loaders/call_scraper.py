import os
import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from pathlib import Path
from django.conf import settings
from flaim.data_loaders.loblaws_scraper import run_loblaws_scraper


def enqueue_loblaws_scraper(url: str, outdir: Path, filter_keyword: str = None, load_into_db: bool = True,
                            dump_to_csv: bool = False):
    """ Submits a Loblaws scraping job to RQ """
    try:
        loblaws_result = run_loblaws_scraper(url=url,
                                             outdir=outdir,
                                             filter_keyword=filter_keyword,
                                             load_into_db=load_into_db,
                                             dump_to_csv=dump_to_csv).delay()
    except AttributeError:
        print("Done!")


if __name__ == "__main__":
    # loblaws_outdir = Path(settings.MEDIA_ROOT)

    """
    DONE
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007001000
    
    TODO
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Minerals/c/LSL002007002000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007005000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007011000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007003000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007009000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007004000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007007000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007006000
    https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/c/LSL002007008000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006001000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006002000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006003000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006004000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006005000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006007000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006008000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006010000
    https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/c/LSL002006011000
    
    
    """

    natural_health_products = Path("/home/forest/Documents/Natural_Health_Products_scrape")

    target_urls = [
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Vitamins/c/LSL002007001000",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Vitamins/c/LSL002007001002",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Vitamins/c/LSL002007001003",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Vitamins/c/LSL002007001004",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Diet-%26-Weight-Supplements/c/LSL002007005001",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Diet-%26-Weight-Supplements/c/LSL002007005002",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Diet-%26-Weight-Supplements/c/LSL002007005003",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Diet-%26-Weight-Supplements/c/LSL002007005004",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003001",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003008",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003003",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003006",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003007",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003009",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003004",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003002",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003005",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Herbal-%26-Natural-Supplements/c/LSL002007003010",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Sports-Nutrition/c/LSL002007004003",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Sports-Nutrition/c/LSL002007004001",
        # "https://www.loblaws.ca/Home-%26-Lifestyle/Diet-%26-Nutrition/Sports-Nutrition/c/LSL002007004004",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Allergy-%26-Sinus/c/LSL002006002000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Cough%2C-Cold-%26-Flu/c/LSL002006003000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Diabetes-Management/c/LSL002006004000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Digestion-%26-Nausea/c/LSL002006005000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/First-Aid/c/LSL002006006000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Foot-Care/c/LSL002006007000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Home-Health-Care/c/LSL002006008000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Pain-%26-Fever-Relief/c/LSL002006010000",
        "https://www.loblaws.ca/Home-%26-Lifestyle/Medicine-%26-Health/Sleep-%26-Snoring-Aids/c/LSL002006011000",
        "",
        "",
        "",

    ]

    for url in target_urls:
        try:
            print(f"Working on {url}")
            enqueue_loblaws_scraper(
                url=url,
                outdir=natural_health_products,
                load_into_db=False,
                dump_to_csv=True)
        except Exception as e:
            print(f"Failed on {url} for some reason - moving to next URL")
            print(e)
            continue
