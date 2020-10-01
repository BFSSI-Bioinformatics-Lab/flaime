import pandas as pd
from django.core.management.base import BaseCommand
from flaim.data_loaders.management.accessories import get_atwater_results
from flaim.database.models import Product, NutritionFacts
from tqdm import tqdm


def calculate_atwater():
    product_df = pd.DataFrame(list(Product.objects.filter(most_recent=True).values()))
    nft_df = pd.DataFrame(list(NutritionFacts.objects.filter(product__most_recent=True).values()))
    df = product_df.merge(nft_df, left_on='id', right_on='product_id')
    df['atwater_result'] = get_atwater_results(df)

    for i, row in tqdm(df.iterrows(), total=len(df), desc="Updating database"):
        product = Product.objects.get(id=row['id_x'])
        product.atwater_result = row['atwater_result']
        product.save()


class Command(BaseCommand):
    help = 'This script will run the Atwater calculation on the most recent products in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f'Calculating Atwater results...'))
        calculate_atwater()
        self.stdout.write(self.style.SUCCESS(f'Done!'))
