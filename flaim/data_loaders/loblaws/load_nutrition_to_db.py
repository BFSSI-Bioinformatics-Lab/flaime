import os
import django

# Need to do this in order to access the flaim database models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from flaim.database.models import LoblawsProduct, NutritionFacts

if __name__ == "__main__":
    products = LoblawsProduct.objects.filter(nutrition_facts_json__isnull=False)
    for p in products:
        nutrition_facts_instance, created = NutritionFacts.objects.get_or_create(product=p.product)
        nutrition_facts_instance.load_ingredients(p.api_data)
        nutrition_facts_instance.load_total_size(p.api_data)
        nutrition_facts_instance.load_loblaws_nutrition_facts_json(p.nutrition_facts_json)

    # nutrition_facts_instance = NutritionFacts.objects.get(product__product_code='21042359_EA')
    # nutrition_facts_instance.parse_loblaws_nutrition_facts_json(
    #     nutrition_facts_instance.product.loblaws_product.nutrition_facts_json)
