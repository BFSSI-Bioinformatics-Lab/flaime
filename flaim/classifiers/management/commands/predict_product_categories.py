import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from flaim.database.models import Product, PredictedCategory
from flaim.classifiers.category_prediction import CategoryPredictor
from flaim.classifiers.category_preprocessing import FLAIME
from flaim.database import models
from tqdm import tqdm

CATEGORY_PREDICTOR_MODEL = Path(__file__).parents[2] / 'data' / 'category_predictor.pkl'


class Command(BaseCommand):
    help = 'This script will run the category prediction model against Product objects in the database and update ' \
           'the corresponding predicted_category field for each. By default, only products with most_recent=True will ' \
           'have their category predicted. '

    def add_arguments(self, parser):
        parser.add_argument('--all_products', action='store_true',
                            help='Call this flag in order to predict categories for ALL products in the database rather'
                                 ' than only those with most_recent=True.')

    def handle(self, *args, **options):
        if options['all_products']:
            self.stdout.write(self.style.SUCCESS(f'Predicting categories for ALL products in database'))
            most_recent_bool = False
        else:
            self.stdout.write(self.style.SUCCESS(f'Predicting categories for recent products in database'))
            most_recent_bool = True

        predictor = CategoryPredictor(CATEGORY_PREDICTOR_MODEL)

        self.stdout.write(self.style.SUCCESS(f'Detected category prediction model version {predictor.model_version}'))

        data = FLAIME(models.Product, models.NutritionFacts, most_recent_bool)
        predictions = predictor.predict(data)

        df = pd.concat([data.product_ids, data.names, predictions], axis=1)
        self.stdout.write(self.style.SUCCESS(f"Found {len(df)} products to update"))
        for i, row in tqdm(df.iterrows(), desc="Predicting categories"):
            predicted_category = PredictedCategory.objects.create(predicted_category=row['Pred 1'],
                                                                  confidence=row['Conf 1'],
                                                                  model_verison=predictor.model_version)
            o = Product.objects.get(id=row['id'])
            o.predicted_category = predicted_category
            o.save()
