import pandas as pd

from django.db.models import F
from flaim.database import models


class ReportData:
    def __init__(self):
        self.df = self._get_data()

    def _get_data(self):
        products = models.Product
        nutrition_facts = models.NutritionFacts
        df1 = pd.DataFrame(list(products.objects
                                .annotate(category_text=F('category__predicted_category_1'))
                                .annotate(manual_category_text=F('category__manual_category'))
                                .annotate(subcategory_text=F('subcategory__predicted_subcategory_1'))
                                .annotate(manual_subcategory_text=F('subcategory__manual_subcategory'))
                                .filter(most_recent=True)
                                .values()))
        df2 = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True)
                                .annotate(product_code=F('product__product_code'))
                                .values()))

        df = df1.merge(df2.drop(columns=['id', 'created', 'modified']),
                       on='product_code').drop(columns=['id', 'created', 'modified', 'product_id'])

        manual_index = df['manual_category_text'].dropna().index
        df['category_text'].loc[manual_index] = df['manual_category_text'].dropna()

        manual_sub_index = df['manual_subcategory_text'].dropna().index
        df['subcategory_text'].loc[manual_sub_index] = df['manual_subcategory_text'].dropna()

        df = df.loc[(df['category_text'] != 'Unknown') & (df['category_text'] != 'Not Food')
                    & (df['category_text'] != 'Uncategorized')]
        df['sugar'] /= 100
        df['brand'] = df['brand'].str.replace('’', "'")

        return df


class StoreReportData(ReportData):
    def __init__(self):
        super().__init__()

    def _get_data(self):
        df = super()._get_data()
        images = models.ProductImage
        df3 = pd.DataFrame(list(images.objects.annotate(product_code=F('product__product_code')).values()))
        df = df.merge(df3, how='outer', on='product_code').drop(columns=['id', 'product_id', 'created', 'modified'])
        return df  #.drop_duplicates(subset='name')
