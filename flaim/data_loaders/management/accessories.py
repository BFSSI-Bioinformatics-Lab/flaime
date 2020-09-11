from typing import Optional
from flaim.database.models import CategoryProductCodeMappingSupport

"""
Accessory methods for data_loaders.management.commands
"""


def find_curated_category(product_code: str) -> Optional[str]:
    """
    Tries to retrieve a manually curated category from the database based on the provided product_code
    returns None if query can't find a match
    """
    try:
        mapping = CategoryProductCodeMappingSupport.objects.get(product_code=product_code)
        return mapping.category
    except CategoryProductCodeMappingSupport.DoesNotExist:
        return None
