# Loblaws scraper script notes

## Product Data
#### 1. product_links_api.py
This script scrapes Loblaws product categories and retrieves URLs for every single product it can find. 
These are stored in JSON files that will be parsed by the next script. 

#### 2. product_detail_api.py
Uses links from the previous script to download the raw data from the Loblaws product API. Stores each product
in an individual JSON file named by its product code. 

#### 3. download_images.py
Parses the product JSON files retrieved with product_detail_api.py to grab the image URLs for each product.
Downloads all images from the Loblaws servers.

#### 4. load_json_to_db.py
Takes the JSON files from the previous step and loads them into the database according to the Product,
LoblawsProduct, and NutritionFacts models. Also loads images. Note that the image dir, data dir, 
and scrape date must all be manually set.
