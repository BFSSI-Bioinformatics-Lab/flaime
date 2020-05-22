import requests
import json
import time
from pathlib import Path
from flaim.data_loaders.loblaws.get_loblaws_categories import generate_category_list

"""
Helper script to collect all Loblaws' product code data. Data retrieved with this script is stored in JSON files
that contain ~48 products each. Product codes can be retrieved from these files and passed to product_detail_api.py to
get ingredients, nutrients, etc. 
"""

SCRAPE_DATE = '2020-04-17'

if __name__ == "__main__":
    outdir = Path(f"/home/forest/Documents/FLAIME/loblaws_data/page_data_{SCRAPE_DATE}")
    outdir.mkdir(exist_ok=True)

    cookies = {
        'lcl_lang_pref': 'en',
        'customer_state': 'anonymous',
        'check': 'true',
        '_sl_session_beat': 'current',
        '_sl_analytics_visitor': 'true',
        '_sl_ping_marker': 'initial',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'Site-Banner': 'loblaw',
        'Content-Type': 'application/json;charset=utf-8',
        # Looks like if the connection is kept alive too long it will be closed by the Loblaws server
        # 'Connection': 'keep-alive',
        'Connection': 'close',
        'Referer': 'https://www.loblaws.ca/Food/c/LSL001000000000?navid=Food',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    # Retrieved list from Loblaws main grocery product page
    subcategories = generate_category_list()

    # Iterate over each subcategory and simulate clicking through every page to get all product codes
    for subcategory in subcategories:
        collect_data = True
        page_number = -1
        while collect_data:
            page_number += 1
            outname = f'{subcategory}_page_{page_number}.json'

            # Skip if we've already retrieved this page
            if (outdir / outname).exists():
                continue

            print(f'Working on {subcategory} - page {page_number}')
            params = (
                ('pageSize', '48'),
                ('pageNumber', page_number),
                ('sort', 'recommended'),
            )

            response = requests.get(f'https://www.loblaws.ca/api/category/{subcategory}/products', headers=headers,
                                    params=params,
                                    cookies=cookies)

            try:
                json_response = response.json()
            except:
                continue

            try:
                product_results = json_response['results']
            except KeyError as e:
                print(f'Encountered issue retrieving response for {subcategory}, page {page_number}')
                print(e)
                continue

            max_pages = json_response['pagination']['totalResults'] / 48
            if page_number >= max_pages:
                collect_data = False

            with open(outdir / outname, 'w') as f:
                json.dump(product_results, f)
            time.sleep(2)
