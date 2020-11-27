from django.views.generic import TemplateView
from django.db.models import F

from flaim.database import models
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_html
import pandas as pd


class DownloadView(TemplateView):
    template_name = 'data/download.html'


class QualityView(TemplateView):
    template_name = 'data/quality.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        df = get_df()

        non_nft_columns = {'product_code', 'name', 'brand', 'description', 'breadcrumbs_text', 'breadcrumbs_array',
                           'batch_id', 'store', 'price', 'price_float', 'price_units', 'upc_code', 'upc_array',
                           'nutrition_available', 'unidentified_nft_format', 'nielsen_product', 'url', 'category_text',
                           'product_id', 'total_size', 'serving_size_raw', 'serving_size', 'serving_size_units'}

        meta_columns = {'batch_id', 'store', 'nutrition_available', 'unidentified_nft_format', 'nielsen_product', 'url',
                        'breadcrumbs_text', 'breadcrumbs_array'}
        info_columns = non_nft_columns - meta_columns
        nft_columns = set(df.columns.tolist()) - non_nft_columns

        context['meta_columns'] = meta_columns
        context['info_columns'] = info_columns
        context['nft_columns'] = nft_columns

        context['product_count'] = df.shape[0]
        context['column_count'] = df.shape[1]
        context['missing_nft'] = f'{df.calories.isnull().sum()/df.shape[0]*100:.1f}%'
        context['completeness'] = f'{(1-df.isnull().sum().sum()/(df.shape[0]*df.shape[1]))*100:.1f}%'
        context['figure1'] = get_missing_nft_graph(df)

        return context


# Fetch dataset
def get_df():
    products = models.Product
    nutrition_facts = models.NutritionFacts
    df1 = pd.DataFrame(list(products.objects
                            .annotate(category_text=F('category__predicted_category_1'))
                            .annotate(manual_category_text=F('category__manual_category'))
                            .filter(most_recent=True)
                            .values()))
    df2 = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True).values()))
    df2.drop(columns=['id', 'created', 'modified'], inplace=True)
    df = df1.merge(df2, left_on='id', right_on='product_id').drop(columns=['id', 'created', 'modified', 'most_recent',
                                                                           'category_id'])
    manual_index = df['manual_category_text'].dropna().index
    df['category_text'].loc[manual_index] = df['manual_category_text'].dropna()
    df = df.loc[(df['category_text'] != 'Unknown') & (df['category_text'] != 'Not Food')]
    df['sugar'] /= 100
    df['brand'] = df['brand'].str.replace('’', "'")

    return df


def get_missing_nft_graph(df):
    plot_df = df.groupby(['category_text', 'nutrition_available']).count()['name'].reset_index()

    fig = px.bar(plot_df.sort_values(by='nutrition_available', ascending=False)
                 .rename(columns={'nutrition_available': 'Product Has NFT'}),
                 x='category_text', y='name', color='Product Has NFT')
    fig.update_layout(xaxis={'categoryorder': 'total descending', 'tickangle': 45, 'title': 'Predicted Category'},
                      yaxis_title='Product Count', height=650, margin=dict(t=30, l=100))

    return to_html(fig, include_plotlyjs=False, full_html=False)

