import requests
import time
import json
from pathlib import Path

PRODUCT_LIST_DIR = Path("/home/forest/loblaws_api/page_data_04022020")
OUTDIR = Path("/home/forest/loblaws_api/product_data_04022020")

DEFAULT_PARAMETERS = {
    'cookies': {
        'lcl_lang_pref': 'en',
        'customer_state': 'anonymous',
        'check': 'true',
        '_sl_session_beat': 'current',
        '_sl_analytics_visitor': 'true',
    },
    'headers': {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en',
        'Site-Banner': 'loblaw',
        # 'Pickup-Location-Id': '1028',
        'Content-Type': 'application/json;charset=utf-8',
        'Connection': 'close',
        # Looks like if the connection is kept alive too long it will be closed by the Loblaws server
        # 'Connection': 'keep-alive',
        'Referer': 'https://www.loblaws.ca/Food/c/LSL001000000000?navid=Food',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
}


def get_product_details(product_code: str, outdir: Path):
    outfile = outdir / f'{product_code}.json'
    if outfile.exists():
        print(f'{product_code} already retrieved\n')
        return

    print(f"Grabbing {product_code}")
    response = requests.get(f"https://www.loblaws.ca/api/product/{product_code}",
                            headers=DEFAULT_PARAMETERS['headers'],
                            cookies=DEFAULT_PARAMETERS['cookies'])
    json_response = response.json()
    with open(str(outfile), 'w') as f:
        json.dump(json_response, f)
    time.sleep(1.5)


def read_product_list_file(product_list: Path) -> list:
    codes = []
    with open(str(product_list), 'r') as f:
        data = json.load(f)
        for product in data:
            codes.append(product['code'])
    return codes


if __name__ == "__main__":
    product_list_files = list(PRODUCT_LIST_DIR.glob("*"))
    for p in product_list_files:
        codes_ = read_product_list_file(p)
        for product_code_ in codes_:
            get_product_details(product_code_, OUTDIR)
