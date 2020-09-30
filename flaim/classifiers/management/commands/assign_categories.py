import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from flaim.data_loaders.management.accessories import find_curated_category
from flaim.database.models import Product, Category
from flaim.classifiers.category_prediction import CategoryPredictor, SubcategoryPredictor
from flaim.classifiers.category_preprocessing import FLAIME
from flaim.database import models
from tqdm import tqdm

CATEGORY_PREDICTOR_MODEL = Path(__file__).parents[2] / 'data' / 'category_predictor.pkl'
SUBCATEGORY_PREDICTOR_MODEL = Path(__file__).parents[2] / 'data' / 'subcategory_predictor.pkl'

User = get_user_model()


class Command(BaseCommand):
    help = 'This script will run the category prediction model against Product objects in the database and update ' \
           'the corresponding category field for each. By default, only products with most_recent=True will ' \
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
        sub_predictor = SubcategoryPredictor(SUBCATEGORY_PREDICTOR_MODEL)

        self.stdout.write(self.style.SUCCESS(f'Detected category prediction model version {predictor.model_version}'))

        data = FLAIME(models.Product, models.NutritionFacts, most_recent_bool)
        predictions = predictor.predict(data)
        sub_predictions = sub_predictor.predict(data, predictions['Pred 1'])

        blank_product = pd.DataFrame.sparse.from_spmatrix(predictor.vectorizers['name'].transform(['']),
                                                          columns=predictor.vectorizers['name'].get_feature_names(),
                                                          index=[0])
        unknown_p = predictor.model.predict(blank_product).max(axis=1)[0]
        unknowns = predictions.loc[predictions['Conf 1'] == unknown_p, 'Pred 1'].index
        predictions.loc[unknowns, 'Pred 1'] = pd.Series('Unknown', index=unknowns)

        df = pd.concat([data.product_ids, data.names, predictions, sub_predictions], axis=1)
        self.stdout.write(self.style.SUCCESS(f"Found {len(df)} products to update"))
        for i, row in tqdm(df.iterrows(), desc="Predicting categories", total=len(df)):
            predicted_category = Category.objects.create(predicted_category_1=row['Pred 1'],
                                                         confidence_1=row['Conf 1'],
                                                         predicted_category_2=row['Pred 2'],
                                                         confidence_2=row['Conf 2'],
                                                         predicted_category_3=row['Pred 3'],
                                                         confidence_3=row['Conf 3'],
                                                         # = row['Sub-Category']
                                                         # = row['Sub-Category Confidence']
                                                         model_version=predictor.model_version)
            o = Product.objects.get(id=row['id'])
            o.category = predicted_category
            o.save()

        # Iterate through all most_recent=True products and set their manual category if it is already known
        # in the database
        for obj in tqdm(Product.objects.filter(most_recent=True), desc="Assigning known categories"):
            curated_category, verified_by = find_curated_category(obj.product_code)
            if curated_category is not None:
                category = obj.category
                category.manual_category = curated_category
                category.verified = True
                category.verified_by = verified_by
                category.save()
                obj.category = category
                obj.save()
