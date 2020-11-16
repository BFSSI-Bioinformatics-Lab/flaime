import pandas as pd
from django.core.management.base import BaseCommand
from django.db.models import Q
from flaim.database.product_mappings import REFERENCE_CATEGORIES_DICT, PRODUCT_STORES
from flaim.database.models import Product, NutritionFacts
from pathlib import Path
from typing import Optional
from datetime import datetime
from django.db.models import F


def get_report(most_recent: bool, categories: Optional[list], stores: Optional[list]) -> pd.DataFrame:
    products = Product.objects.all()
    products = products.filter(most_recent=most_recent)
    nutrition = NutritionFacts.objects.filter(product__most_recent=most_recent)

    # Filter queryset by categories
    if categories is not None:
        products = products.filter(
            Q(category__predicted_category_1__in=categories) | Q(
                category__manual_category__in=categories)
        )
        nutrition = nutrition.filter(
            Q(product__category__predicted_category_1__in=categories) | Q(
                product__category__manual_category__in=categories)
        )

    if stores is not None:
        products = products.filter(
            Q(store__in=stores) | Q(
                store__in=stores)
        )
        nutrition = nutrition.filter(
            Q(product__store__in=stores) | Q(
                product__store__in=stores)
        )

    # Add more informative columns for category/subcategory
    products = products.annotate(predicted_category=F('category__predicted_category_1'))
    products = products.annotate(predicted_subcategory=F('subcategory__predicted_subcategory_1'))
    products = products.annotate(manual_category=F('category__manual_category'))
    products = products.annotate(manual_subcategory=F('subcategory__manual_subcategory'))

    product_df = pd.DataFrame(list(products.values()))
    nft_df = pd.DataFrame(list(nutrition.values()))
    df = product_df.merge(nft_df, left_on='id', right_on='product_id')
    return df


class Command(BaseCommand):
    help = 'Export a full product report to a .csv file with ease. Can filter on a variety of options.'

    def add_arguments(self, parser):
        parser.add_argument('--outdir',
                            type=str,
                            required=True,
                            help='Path to export reports')
        parser.add_argument('--all_products',
                            action='store_true',
                            default=False,
                            help='Sets most_recent=False when filtering the product set. '
                                 'Beware, this will make the script run considerably slower.')
        parser.add_argument('--categories',
                            type=str,
                            nargs='+',
                            default=None,
                            choices=list(REFERENCE_CATEGORIES_DICT.keys()),
                            help='Filter queryset to only the specified categories. Can take multiple categories at '
                                 'once, delimited by a space e.g. --categories "Soups" "Beverages" will filter the '
                                 'queryset to only contain products from the Soups and Beverages categories.')
        parser.add_argument('--stores',
                            type=str,
                            nargs='+',
                            default=None,
                            choices=[x[0] for x in PRODUCT_STORES],
                            help='Filter queryset to only selected stores. e.g. LOBLAWS,WALMART')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f'Retrieving product report data'))

        # Prepare most_recent
        most_recent = True
        if options['all_products']:
            most_recent = False

        # Prepare categories
        if options['categories'] is not None:
            categories = [x for x in options['categories']]
        else:
            categories = None

        if options['stores'] is not None:
            stores = [x for x in options['stores']]
        else:
            stores = None

        # Create outdir if it does not exist
        outdir = Path(options['outdir'])
        if not outdir.exists():
            outdir.mkdir()

        df = get_report(most_recent, categories, stores)
        outcsv = outdir / f'product_report_{datetime.today().strftime("%Y-%m-%d")}.csv'
        df.to_csv(outcsv, index=False)

        self.stdout.write(self.style.SUCCESS(f'Done! Report is available at {outcsv}'))
