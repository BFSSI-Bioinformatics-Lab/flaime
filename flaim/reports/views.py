import re
from functools import partial
from operator import is_not
from textwrap import wrap
from urllib.parse import unquote

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.views.generic import TemplateView
from numpy.linalg import LinAlgError
from plotly.express.colors import qualitative
from plotly.io import to_html

from flaim.database import models
from flaim.database.product_mappings import PRODUCT_STORES, REFERENCE_CATEGORIES_DICT, \
    REFERENCE_SUBCATEGORIES_CODING_DICT


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class SubcategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/subcategory_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_df = get_plot_df()

        context['subcategory'] = self.kwargs['subcategory']
        # Figure out parent category for image display
        for category, subcategories in REFERENCE_CATEGORIES_DICT.items():
            if self.kwargs['subcategory'] in subcategories:
                context['category'] = category
                context['image'] = category.lower()
        subcategories = list(
            set(REFERENCE_SUBCATEGORIES_CODING_DICT.values()).intersection(set(plot_df['subcategory_text'].unique())))
        subcategories.sort()
        context['subcategories'] = subcategories

        plot_df = plot_df.loc[plot_df['category_text'] == context['category']]

        context['category_count'] = plot_df['subcategory_text'].nunique()
        medians = plot_df.groupby('subcategory_text').median()

        context['sodium_rank'] = get_rank_suffix(medians.sort_values(by='sodium_dv', ascending=False)
                                                 .index.get_loc(context['subcategory']))
        context['fat_rank'] = get_rank_suffix(medians.sort_values(by='saturatedfat_dv', ascending=False)
                                              .index.get_loc(context['subcategory']))
        context['sugar_rank'] = get_rank_suffix(medians.sort_values(by='sugar', ascending=False)
                                                .index.get_loc(context['subcategory']))

        # plot_df = plot_df.loc[plot_df['category_text'] == context['category']]
        plot_df = plot_df.loc[plot_df['subcategory_text'] == context['subcategory']]

        ingredient_count = plot_df['ingredients'].str.findall(',').fillna('').apply(lambda row: len(row) + 1)
        context['ingredient_q25'] = int(ingredient_count.quantile(0.25))
        context['ingredient_q75'] = int(ingredient_count.quantile(0.75))

        # This gets the 3 most common ingredients but does not preprocess the ingredient lists
        common_ingredients = pd.Series(' '.join(plot_df['ingredients'].fillna('').str.lower().tolist())
                                       .split(',')).value_counts().head(3).index.tolist()
        if len(common_ingredients) >= 3:
            context['common_ingredients'] = f'The three most common ingredients in this category are \
            {common_ingredients[0]}, {common_ingredients[1]}, and {common_ingredients[2]}.'
        elif len(common_ingredients) == 2:
            context['common_ingredients'] = f'The two most common ingredients in this category are \
            {common_ingredients[0]} and {common_ingredients[1]}.'
        # Seems unlikely to only have one ingredient, note it can still have 0 ingredients in which case this sentence
        # will not be displayed
        elif len(common_ingredients) == 1:
            context['common_ingredients'] = f'The only ingredient in this category is {common_ingredients[0]}.'

        # Top bar
        context['product_count'] = plot_df.shape[0]
        context['store_count'] = plot_df['store'].nunique()
        context['manual_category_count'] = plot_df['manual_category_text'].dropna().shape[0]
        context['predicted_category_count'] = context['product_count'] - context['manual_category_count']

        context['calorie_median'] = f'{plot_df.calories.median():.0f}'

        context['sodium_color'] = get_nutrient_color(plot_df.sodium_dv.median())
        context['sodium_median'] = f'{plot_df.sodium_dv.median() * 100:.0f}%'

        context['fat_color'] = get_nutrient_color(plot_df.saturatedfat_dv.median())
        context['fat_median'] = f'{plot_df.saturatedfat_dv.median() * 100:.0f}%'

        context['sugar_color'] = get_nutrient_color(plot_df.sugar.median())
        context['sugar_median'] = f'{plot_df.sugar.median() * 100:.0f}%'

        # Visualizations
        context['figure1'] = get_nutrient_distribution_plot(plot_df)
        return context


class CategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/category_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_df = get_plot_df()

        context['product_categories'] = REFERENCE_CATEGORIES_DICT.keys()

        # set default category
        if 'category' not in self.kwargs:
            context['category'] = plot_df['category_text'].value_counts().index[0]
        else:
            # pulls category from URL e.g. /reports/category/Beverages
            context['category'] = unquote(self.kwargs['category'])

        context['category_count'] = plot_df['category_text'].nunique()
        medians = plot_df.groupby('category_text').median()

        context['sodium_rank'] = get_rank_suffix(medians.sort_values(by='sodium_dv', ascending=False)
                                                 .index.get_loc(context['category']))
        context['fat_rank'] = get_rank_suffix(medians.sort_values(by='saturatedfat_dv', ascending=False)
                                              .index.get_loc(context['category']))
        context['sugar_rank'] = get_rank_suffix(medians.sort_values(by='sugar', ascending=False)
                                                .index.get_loc(context['category']))

        plot_df = plot_df.loc[plot_df['category_text'] == context['category']]

        ingredient_count = plot_df['ingredients'].str.findall(',').fillna('').apply(lambda row: len(row) + 1)
        context['ingredient_q25'] = int(ingredient_count.quantile(0.25))
        context['ingredient_q75'] = int(ingredient_count.quantile(0.75))

        # This gets the 3 most common ingredients but does not preprocess the ingredient lists
        common_ingredients = pd.Series(' '.join(plot_df['ingredients'].fillna('').str.lower().tolist())
                                       .split(',')).value_counts().head(3).index.tolist()
        if len(common_ingredients) >= 3:
            context['common_ingredients'] = f'The three most common ingredients in this category are \
            {common_ingredients[0]}, {common_ingredients[1]}, and {common_ingredients[2]}.'
        elif len(common_ingredients) == 2:
            context['common_ingredients'] = f'The two most common ingredients in this category are \
            {common_ingredients[0]} and {common_ingredients[1]}.'
        # Seems unlikely to only have one ingredient, note it can still have 0 ingredients in which case this sentence
        # will not be displayed
        elif len(common_ingredients) == 1:
            context['common_ingredients'] = f'The only ingredient in this category is {common_ingredients[0]}.'

        # Top bar
        context['image'] = context['category'].lower()
        context['product_count'] = plot_df.shape[0]
        context['store_count'] = plot_df['store'].nunique()
        context['manual_category_count'] = plot_df['manual_category_text'].dropna().shape[0]
        context['predicted_category_count'] = context['product_count'] - context['manual_category_count']

        context['calorie_median'] = f'{plot_df.calories.median():.0f}'

        context['sodium_color'] = get_nutrient_color(plot_df.sodium_dv.median())
        context['sodium_median'] = f'{plot_df.sodium_dv.median() * 100:.0f}%'

        context['fat_color'] = get_nutrient_color(plot_df.saturatedfat_dv.median())
        context['fat_median'] = f'{plot_df.saturatedfat_dv.median() * 100:.0f}%'

        context['sugar_color'] = get_nutrient_color(plot_df.sugar.median())
        context['sugar_median'] = f'{plot_df.sugar.median() * 100:.0f}%'

        # Visualizations
        context['figure1'] = get_nutrient_distribution_plot(plot_df)
        return context


class BrandView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/store_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_stores'] = [x[0] for x in PRODUCT_STORES]

        plot_df = get_plot_df()

        context['category_count'] = plot_df['category_text'].nunique()

        if 'store' not in self.kwargs:
            context['store'] = np.random.choice(plot_df['store'].unique())  # set default category
        else:
            context['store'] = unquote(
                self.kwargs['store'].upper())  # pulls category from URL e.g. /reports/store/Loblaws

        plot_df = plot_df.loc[plot_df['store'] == context['store']]

        context['manual_category_count'] = plot_df['manual_category_text'].dropna().shape[0]

        # This can probably be split off into a utility function
        common_categories = plot_df['category_text'].value_counts().head(3).to_dict()
        sen = ', '.join([f'{key} ({common_categories[key]} products)' for key in common_categories])
        sen_par = sen.rpartition(', ')
        context['common_categories'] = sen_par[0] + ', and ' + sen_par[-1]

        # above function would be repeated here
        common_brands = plot_df['brand'].value_counts().head(5).to_dict()
        sen = ', '.join([f'{key} ({common_brands[key]} products)' for key in common_brands])
        sen_par = sen.rpartition(', ')
        context['common_brands'] = sen_par[0] + ', and ' + sen_par[-1]

        # Top bar
        context['image'] = context['store'].lower()
        context['store'] = context['store'].capitalize()
        context['product_count'] = plot_df.shape[0]
        products_with_nft = plot_df.shape[0] - plot_df.calories.isnull().sum()
        # context['missing_nft'] = f'{plot_df.calories.isnull().sum()/plot_df.shape[0]*100:.1f}%'
        context['has_nft'] = products_with_nft
        context['has_nft_percent'] = f'{products_with_nft} ({products_with_nft / plot_df.shape[0] * 100:.0f}%)'

        context['sodium_products_over_15'] = plot_df[plot_df.sodium_dv > 0.15].shape[0]
        sodium_percent = context['sodium_products_over_15'] / products_with_nft * 100
        context['sodium_products_percent'] = f'{sodium_percent:.1f}%'

        context['fat_products_over_15'] = plot_df[plot_df.saturatedfat_dv > 0.15].shape[0]
        fat_percent = context['fat_products_over_15'] / products_with_nft * 100
        context['fat_products_percent'] = f'{fat_percent:.1f}%'

        context['sugar_products_over_15'] = plot_df[plot_df.sugar > 0.15].shape[0]
        sugar_percent = context['sugar_products_over_15'] / products_with_nft * 100
        context['sugar_products_percent'] = f'{sugar_percent:.1f}%'

        cols = ['name', 'image_path', 'image_number', 'image_label']
        pivot_df = pd.concat([plot_df['name'], plot_df[cols].pivot(columns='image_label', values=['image_path'])],
                             axis=1)
        pivot_df.columns = [str(c) for c in pivot_df.columns]
        flat_cols = list(set(pivot_df.columns) - {'name'})

        def make_list(x):
            return list(filter(partial(is_not, np.nan), list(x)))
        agg_df = pivot_df.groupby('name').agg({c: lambda x: make_list(x) for c in flat_cols})
        if "('image_path', 'nutrition')" in flat_cols:
            img_diff_df = plot_df[['name', 'calories']].copy().drop_duplicates(subset='name')
            img_diff_df = img_diff_df.merge(agg_df["('image_path', 'nutrition')"], right_index=True, left_on='name')
            img_diff_df['OCR failed'] = (img_diff_df['calories'].isnull()) & \
                                        (img_diff_df["('image_path', 'nutrition')"].apply(len) > 0)
            ocr_fail_with_image = img_diff_df.loc[
                img_diff_df["('image_path', 'nutrition')"].apply(len) > 0, 'OCR failed'].value_counts()
            context['nft_ocr'] = ocr_fail_with_image[False]
            context['failed_ocr'] = ocr_fail_with_image[True]
        else:
            context['nft_ocr'] = 0
            context['failed_ocr'] = 0

        context['has_ingredients'] = len(plot_df['ingredients'].dropna())
        plot_df['allergy'] = plot_df['ingredients'].str.contains('contain', flags=re.IGNORECASE).fillna(False)
        context['has_allergy_info'] = len(plot_df.loc[plot_df['allergy'], ['name', 'ingredients']].drop_duplicates())

        pack_img = agg_df["('image_path', nan)"].apply(len)
        if "('image_path', 'other')" in flat_cols:
            pack_img += agg_df["('image_path', 'other')"].apply(len)
        pack_img.name = 'pack images'
        context['front_img_mean'] = f'{pack_img.mean():.1f}'
        context['missing_img'] = pack_img.value_counts()[0]
        context['has_img'] = pack_img.value_counts()[1:].sum()

        complete_df = plot_df[['name', 'calories', 'allergy']].drop_duplicates().merge(pack_img, left_on='name',
                                                                                       right_index=True)
        complete_df['complete'] = (~complete_df['calories'].isnull()) & \
                                  (complete_df['pack images'] > 0) & complete_df['allergy']
        context['complete'] = complete_df['complete'].value_counts()[True]

        # Visualizations
        context['figure1'] = get_category_nutrient_distribution_plot(plot_df)
        return context


def get_nutrient_color(value):
    return 'text-success' if value <= 0.15 else 'text-danger'


def get_rank_suffix(i):
    i = i + 1
    if i >= 11 and 11 <= int(str(i)[-2:]) <= 13:
        return f'{i}th'
    remainder = i % 10
    if remainder == 1:
        return f'{i}st'
    elif remainder == 2:
        return f'{i}nd'
    elif remainder == 3:
        return f'{i}rd'
    else:
        return f'{i}th'


# Fetch dataset
def get_plot_df():
    products = models.Product
    nutrition_facts = models.NutritionFacts
    images = models.ProductImage
    df1 = pd.DataFrame(list(products.objects
                            .annotate(category_text=F('category__predicted_category_1'))
                            .annotate(manual_category_text=F('category__manual_category'))
                            .annotate(subcategory_text=F('subcategory__predicted_subcategory_1'))
                            .annotate(manual_subcategory_text=F('subcategory__manual_subcategory'))
                            .filter(most_recent=True)
                            .values()))
    df2 = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True).values()))
    df3 = pd.DataFrame(list(images.objects.filter(product__most_recent=True).values()))

    df = df1.merge(df2.drop(columns=['id', 'created', 'modified']),
                   left_on='id', right_on='product_id').drop(columns=['created', 'modified', 'product_id'])
    df = df.merge(df3.drop(columns=['id']), how='outer',
                  left_on='id', right_on='product_id').drop(columns=['id', 'product_id', 'created', 'modified'])
    # df.to_csv('/home/brian/Code/flaime/data/git_with_images.csv', index=False)

    manual_index = df['manual_category_text'].dropna().index
    df['category_text'].loc[manual_index] = df['manual_category_text'].dropna()

    manual_sub_index = df['manual_subcategory_text'].dropna().index
    df['subcategory_text'].loc[manual_sub_index] = df['manual_subcategory_text'].dropna()

    df = df.loc[(df['category_text'] != 'Unknown') & (df['category_text'] != 'Not Food')
                & (df['category_text'] != 'Uncategorized')]
    df['sugar'] /= 100
    df['brand'] = df['brand'].str.replace('’', "'")

    return df


# Figure generation
def get_nutrient_distribution_plot(df):
    nutrients = ['sodium_dv', 'saturatedfat_dv', 'sugar']

    try:
        fig = ff.create_distplot(df[nutrients].dropna(how='all').fillna(0).T.values,
                                 ['Sodium', 'Saturated Fat', 'Sugar'], colors=qualitative.Vivid, histnorm='probability',
                                 bin_size=0.01, show_rug=False, )
        fig.update_layout(
            width=1100,
            font_size=18,
            xaxis=dict(
                title='Daily Value',
                tickformat='%',
                showgrid=True,
                range=[0, min([1, max(df[n].quantile(0.95) for n in nutrients)])]
            ),
            yaxis=dict(
                tickformat='%',
                title='Proportion of Products'
            ),
            margin=dict(
                l=100,
                r=20,
                b=30,
                t=30,
            ),
            legend_title='Nutrients'
        )

        fig.add_shape(dict(
            type='line',
            yref='paper',
            x0=0.15,
            y0=0,
            x1=0.15,
            y1=1,
            line=dict(
                color='Black',
                width=2
            )))

        fig.add_annotation(text='← Low in Nutrient',
                           yref='paper',
                           x=0.145, y=1,
                           showarrow=False,
                           xanchor='right',
                           yanchor='bottom',
                           font_color='green')
        fig.add_annotation(text='High in Nutrient →',
                           yref='paper',
                           x=0.155, y=1,
                           showarrow=False,
                           xanchor='left',
                           yanchor='bottom',
                           font_color='red')
    except LinAlgError:
        return "Graph can't be displayed."
    except ValueError:
        return "Not enough data to generate graph."

    return to_html(fig, include_plotlyjs=False, full_html=False)


def get_category_nutrient_distribution_plot(df):
    def over_15(row):
        return 1 if row > 0.15 else 0

    nutrients = ['sodium_dv', 'saturatedfat_dv', 'sugar']
    nutrient_map = {'sodium_dv': 'Sodium', 'saturatedfat_dv': 'Saturated Fat', 'sugar': 'Sugar'}
    categories = ['Beverages', 'Cereals and Other Grain Products', 'Dairy Products and Substitutes',
                  'Meat and Poultry, Products and Substitutes', 'Snacks']

    category_labels = ['<br>'.join(wrap(c, 20)) for c in categories]

    plot_df = df.loc[df['category_text'].isin(categories)]

    for n in nutrients:
        plot_df[f'{n}_count'] = plot_df[n].apply(lambda row: over_15(row))

    plot_df = plot_df[['category_text'] + [f'{n}_count' for n in nutrients]].groupby(
        'category_text').sum().reindex(categories)

    data = [
        go.Bar(name=nutrient_map[nutrient], x=category_labels, y=plot_df[f'{nutrient}_count']) for nutrient in nutrients
    ]

    layout = dict(
        width=1100,
        font_size=18,
        margin=dict(
            l=100,
            r=20,
            b=20,
            t=30,
        ),
        yaxis_title='Products Exceeding Threshold',
        xaxis=dict(
            title='Food Category',
            showgrid=True,
            tickson='boundaries',
            tickangle=0,
        ),
    )

    fig = go.Figure(data=data, layout=layout)

    return to_html(fig, include_plotlyjs=False, full_html=False)
