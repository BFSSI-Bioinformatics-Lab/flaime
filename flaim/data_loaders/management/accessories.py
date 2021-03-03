from typing import Optional, Tuple
from tqdm import tqdm
import pandas as pd

from flaim.database.models import CategoryProductCodeMappingSupport, Product, VarietyPackProductCodeMappingSupport

"""
Accessory methods for data_loaders.management.commands
"""


def assign_variety_pack_flag():
    # Iterate through all most_recent=True products and set their manual category if it is already known
    # in the database
    for obj in tqdm(Product.objects.filter(most_recent=True), desc="Assigning known variety pack flags"):
        curated_variety_pack_flag = find_curated_variety_pack_flag(obj.product_code)
        obj.variety_pack = curated_variety_pack_flag
        obj.save()


def find_curated_variety_pack_flag(product_code: str) -> bool:
    """
    Given a product code, queries the VarietyPackProductCode support table to find if it has been flagged as a variety
    pack or not. Note the value defaults to False since most products are likely not variety packs.
    """
    try:
        obj = VarietyPackProductCodeMappingSupport.objects.get(product_code=product_code)
        return obj.variety_pack
    except VarietyPackProductCodeMappingSupport.DoesNotExist:
        return False


def find_curated_category(product_code: str) -> [Tuple[Optional[str], Optional[str], Optional[str]]]:
    """
    Tries to retrieve a manually curated category from the database based on the provided product_code
    returns None if query can't find a match
    """
    try:
        obj = CategoryProductCodeMappingSupport.objects.get(product_code=product_code)
        return obj.category, obj.subcategory, obj.verified_by
    except CategoryProductCodeMappingSupport.DoesNotExist:
        return None, None, None


def get_atwater_results(df: pd.DataFrame) -> pd.Series:
    substitutes = ['advantame', 'acesulfame', 'aspartame', 'erythritol', 'hydrogenated starch hydrolysates', 'isomalt',
                   'isolmalt', 'lactitol', 'maltitol', 'mannitol', 'monk fruit extract', 'neotame', 'sorbitol',
                   'saccharin', 'sucralose', 'thaumatin', 'xylitol']
    columns = ['ingredients', 'totalcarbohydrate', 'protein', 'totalfat', 'dietaryfiber', 'calories']
    test_results = ['Within Threshold', 'High Fiber', 'Contains Substitute', 'Investigation Required',
                    'Missing Information']

    def contains_substitute(row):
        for s in substitutes:
            if s in row:
                return s
        return 'none'

    def final_pass(row):
        if row['pass']:
            return test_results[0]
        elif row['pass-fiber']:
            return test_results[1]
        elif row['substitute'] != 'none':
            return test_results[2]
        else:
            return test_results[3]

    a_df = df[['name'] + columns].dropna(how='any', subset=['calories']).dropna(how='all', subset=columns)
    a_df['atwater'] = a_df['totalcarbohydrate'].fillna(0) * 4 + a_df['protein'].fillna(0) * 4 + \
                      a_df['totalfat'].fillna(0) * 9
    a_df['atwater-fiber'] = a_df['atwater'] - a_df['dietaryfiber'].fillna(0) * 4
    a_df['difference'] = ((a_df['calories'] - a_df['atwater']) / a_df['calories']).fillna(0)
    a_df['difference-fiber'] = ((a_df['calories'] - a_df['atwater-fiber']) / a_df['calories']).fillna(0)
    a_df['pass'] = ((a_df['difference'].abs() < 0.2) | ((a_df['calories'] - a_df['atwater']).abs() < 13.5))  # | \
    a_df['pass-fiber'] = ((a_df['difference-fiber'].abs() < 0.2) | ((a_df['calories'] - a_df['atwater']).abs() < 13.5))
    a_df['substitute'] = a_df['ingredients'].str.lower().fillna('').apply(contains_substitute)

    return a_df.apply(final_pass, axis=1).reindex(df.index).fillna(test_results[4])
