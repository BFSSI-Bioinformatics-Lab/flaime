import re
from dataclasses import dataclass
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


@dataclass
class BaseScraper:
    """ Base class to load up the Selenium driver """
    url: str = 'https://www.loblaws.ca/Food/c/LSL001000000000?navid=flyout-L2-Food'

    @staticmethod
    def load_driver():
        """
        Loads up Google Chrome with Selenium
        :return: WebDriver object
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        print(f"Loaded driver successfully: {driver}")
        return driver


def scrape_categories() -> list:
    base = BaseScraper()

    driver = base.load_driver()
    driver.get(base.url)

    _ = WebDriverWait(driver=driver, timeout=15).until(
        ec.presence_of_element_located((By.CLASS_NAME, "category-navigation")))

    # Click see all
    driver.find_element_by_class_name("category-navigation__button").click()

    categories = driver.find_element_by_class_name("category-navigation")
    categories_all = categories.find_elements_by_class_name("category-navigation-item")

    regex = r"/LSL$/.*[?]"

    product_codes = []
    for category in categories_all:
        href = category.find_element_by_xpath("a").get_attribute("href")
        match = re.search(regex, href)
        code = None
        if match:
            code = match.group().replace("?", "")
        if code is not None:
            product_codes.append(code)

    return product_codes


def generate_category_list() -> list:
    expected_categories = ["LSL001050000000",
                           "LSL001001000000",
                           "LSL001002009000",
                           "LSL001003000000",
                           "LSL001004000000",
                           "LSL001005000000",
                           "LSL001006000000",
                           "LSL001007000000",
                           "LSL001002000000",
                           "LSL001008000000",
                           "LSL001009000000",
                           "LSLC017016000000",
                           "LSL001010000000",
                           "LSL001011000000",
                           "LSL017030000000000",
                           "LSL0170160000000",
                           "LSL017010000000",
                           "LSL001016000001",  # cold and flu, lots of junk here

                           # Baby care, includes formula and feeding stuff but also diapers and other non-food products
                           # "LSL002001000000",

                           "LSL001012000000",
                           "LSL001020007000",
                           "LSL001030000000",
                           "LSL001017000000",
                           "LSL001022000000"]
    scraped_categories = scrape_categories()
    all_categories = list(set(expected_categories + scraped_categories))
    return all_categories


if __name__ == "__main__":
    categories_ = generate_category_list()
    print(categories_)
