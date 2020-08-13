import json
from pathlib import Path
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.conf import settings
from django.db import IntegrityError
from django.core.management.base import BaseCommand
from flaim.database.models import Product, PredictedCategory
from tqdm import tqdm
import pandas as pd
from flaim.classifiers.category_prediction import Predictor
from flaim.classifiers.preprocessing import FLAIME
from flaim.database import models

# TODO: set this in .env and read it from settings
CATEGORY_PREDICTOR_MODEL = Path("/home/forest/PycharmProjects/flaim/flaim/classifiers/data/model_int_test.pkl")


class Command(BaseCommand):
    help = 'This script will run the category prediction model against Product objects in the database and update ' \
           'the corresponding predicted_category field for each. By default, only products with most_recent=True will ' \
           'have their category predicted. '

    def add_arguments(self, parser):
        parser.add_argument('--all_products', action='store_true',
                            help='Call this flag in order to predict categories for ALL '
                                 'products in the database rather than only those with '
                                 'most_recent=True')

    def handle(self, *args, **options):
        if options['all_products']:
            self.stdout.write(self.style.SUCCESS(f'Predicting categories for ALL products in database '
                                                 f'(actually this does not work yet, sorry!)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Predicting categories for recent products in database'))

        predictor = Predictor(CATEGORY_PREDICTOR_MODEL)
        data = FLAIME(models.Product, models.NutritionFacts)
        predictions = predictor.predict(data)

        df = pd.concat([data.product_ids, data.names, predictions], axis=1)
        for i, row in df.iterrows():
            predicted_category = PredictedCategory.objects.create(predicted_category=row['Pred 1'],
                                                                  confidence=row['Conf 1'],
                                                                  model_verison="dev-test")
            o = Product.objects.get(id=row['id'])
            o.predicted_category = predicted_category
            o.save()
            self.stdout.write(self.style.SUCCESS(f"Set predicted category for {o} to {predicted_category}"))
