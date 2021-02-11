import re
from functools import partial
from operator import is_not
from urllib.parse import unquote

import numpy as np
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from flaim.database.product_mappings import PRODUCT_STORES, REFERENCE_CATEGORIES_DICT, \
    REFERENCE_SUBCATEGORIES_CODING_DICT
from flaim.reports.data import ReportData, StoreReportData
from flaim.reports.util import get_nutrient_color, get_rank_suffix
from flaim.reports.plots import nutrient_distribution_plot, category_nutrient_distribution_plot


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class SubcategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/subcategory_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = ReportData()
        df = data.df.copy()  # temp copy
        plot_df = df.drop_duplicates(subset='name')

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
        context['figure1'] = nutrient_distribution_plot(plot_df)
        return context


class CategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/category_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = ReportData()
        df = data.df.copy()  # temp copy

        context['product_categories'] = REFERENCE_CATEGORIES_DICT.keys()

        # set default category
        if 'category' not in self.kwargs:
            context['category'] = df['category_text'].value_counts().index[0]
        else:
            # pulls category from URL e.g. /reports/category/Beverages
            context['category'] = unquote(self.kwargs['category'])

        context['category_count'] = df['category_text'].nunique()
        medians = df.groupby('category_text').median()

        context['sodium_rank'] = get_rank_suffix(medians.sort_values(by='sodium_dv', ascending=False)
                                                 .index.get_loc(context['category']))
        context['fat_rank'] = get_rank_suffix(medians.sort_values(by='saturatedfat_dv', ascending=False)
                                              .index.get_loc(context['category']))
        context['sugar_rank'] = get_rank_suffix(medians.sort_values(by='sugar', ascending=False)
                                                .index.get_loc(context['category']))

        df = df.loc[df['category_text'] == context['category']]

        ingredient_count = df['ingredients'].str.findall(',').fillna('').apply(lambda row: len(row) + 1)
        context['ingredient_q25'] = int(ingredient_count.quantile(0.25))
        context['ingredient_q75'] = int(ingredient_count.quantile(0.75))

        # This gets the 3 most common ingredients but does not preprocess the ingredient lists
        common_ingredients = pd.Series(' '.join(df['ingredients'].fillna('').str.lower().tolist())
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
        context['product_count'] = df.shape[0]
        context['store_count'] = df['store'].nunique()
        context['manual_category_count'] = df['manual_category_text'].dropna().shape[0]
        context['predicted_category_count'] = context['product_count'] - context['manual_category_count']

        context['calorie_median'] = f'{df.calories.median():.0f}'

        context['sodium_color'] = get_nutrient_color(df.sodium_dv.median())
        context['sodium_median'] = f'{df.sodium_dv.median() * 100:.0f}%'

        context['fat_color'] = get_nutrient_color(df.saturatedfat_dv.median())
        context['fat_median'] = f'{df.saturatedfat_dv.median() * 100:.0f}%'

        context['sugar_color'] = get_nutrient_color(df.sugar.median())
        context['sugar_median'] = f'{df.sugar.median() * 100:.0f}%'

        # Visualizations
        context['figure1'] = nutrient_distribution_plot(df)
        return context


class BrandView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/store_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_stores'] = [x[0] for x in PRODUCT_STORES]
        data = StoreReportData()
        df = data.df.copy()

        context['category_count'] = df['category_text'].nunique()

        if 'store' not in self.kwargs:
            context['store'] = np.random.choice(df['store'].unique())  # set default category
        else:
            context['store'] = unquote(
                self.kwargs['store'].upper())  # pulls category from URL e.g. /reports/store/Loblaws

        df = df.loc[df['store'] == context['store']]

        context['manual_category_count'] = df['manual_category_text'].dropna().shape[0]

        # This can probably be split off into a utility function
        common_categories = df['category_text'].value_counts().head(3).to_dict()
        sen = ', '.join([f'{key} ({common_categories[key]} products)' for key in common_categories])
        sen_par = sen.rpartition(', ')
        context['common_categories'] = sen_par[0] + ', and ' + sen_par[-1]

        # above function would be repeated here
        common_brands = df['brand'].value_counts().head(5).to_dict()
        sen = ', '.join([f'{key} ({common_brands[key]} products)' for key in common_brands])
        sen_par = sen.rpartition(', ')
        context['common_brands'] = sen_par[0] + ', and ' + sen_par[-1]

        # Top bar
        context['image'] = context['store'].lower()
        context['store'] = context['store'].capitalize()
        context['product_count'] = df.shape[0]
        products_with_nft = df.shape[0] - df.calories.isnull().sum()
        # context['missing_nft'] = f'{plot_df.calories.isnull().sum()/plot_df.shape[0]*100:.1f}%'
        context['has_nft'] = products_with_nft
        context['has_nft_percent'] = f'{products_with_nft} ({products_with_nft / df.shape[0] * 100:.0f}%)'

        context['sodium_products_over_15'] = df[df.sodium_dv > 0.15].shape[0]
        sodium_percent = context['sodium_products_over_15'] / products_with_nft * 100
        context['sodium_products_percent'] = f'{sodium_percent:.1f}%'

        context['fat_products_over_15'] = df[df.saturatedfat_dv > 0.15].shape[0]
        fat_percent = context['fat_products_over_15'] / products_with_nft * 100
        context['fat_products_percent'] = f'{fat_percent:.1f}%'

        context['sugar_products_over_15'] = df[df.sugar > 0.15].shape[0]
        sugar_percent = context['sugar_products_over_15'] / products_with_nft * 100
        context['sugar_products_percent'] = f'{sugar_percent:.1f}%'

        cols = ['name', 'image_path', 'image_number', 'image_label']
        labels = ['none', 'other', 'nutrition', 'ingredients', 'nutrition_american']
        pivot_df = pd.concat([df['name'], df[cols].pivot(columns='image_label', values=['image_path'])], axis=1)
        names = pivot_df.pop('name')
        pivot_df.columns = [label if label in labels else 'none' for path, label in pivot_df.columns]
        pivot_columns = pivot_df.columns
        pivot_df = pd.concat([names, pivot_df], axis=1)

        def make_list(x):
            return list(filter(partial(is_not, np.nan), list(x)))

        agg_df = pivot_df.groupby('name').agg({c: lambda x: make_list(x) for c in pivot_columns})
        if 'other' in agg_df:
            agg_df['none'] = agg_df['none'] + agg_df['other']
            agg_df.drop(columns=['other'], inplace=True)

        if 'nutrition' in agg_df:
            if 'nutrition_american' in agg_df:
                agg_df['nutrition'] = agg_df['nutrition'] + agg_df['nutrition_american']
                agg_df.drop(columns=['nutrition_american'], inplace=True)
            img_diff_df = df[['name', 'calories']].copy()
            img_diff_df = img_diff_df.merge(agg_df['nutrition'], right_index=True, left_on='name')
            img_diff_df['OCR failed'] = (img_diff_df['calories'].isnull()) & \
                                        (img_diff_df['nutrition'].apply(len) > 0)
            ocr_fail_with_image = img_diff_df.loc[
                img_diff_df['nutrition'].apply(len) > 0, 'OCR failed'].value_counts()
            context['nft_ocr'] = ocr_fail_with_image[False]
            context['failed_ocr'] = ocr_fail_with_image[True]
        else:
            context['nft_ocr'] = 0
            context['failed_ocr'] = 0

        context['has_ingredients'] = len(df['ingredients'].dropna())
        df['allergy'] = df['ingredients'].str.contains('contain', flags=re.IGNORECASE).fillna(False)
        context['has_allergy_info'] = len(df.loc[df['allergy'], ['name', 'ingredients']])

        pack_img = agg_df['none'].apply(len)
        pack_img.name = 'pack images'
        context['front_img_mean'] = f'{pack_img.mean():.1f}'
        context['missing_img'] = len(pack_img.loc[pack_img == 0])
        context['has_img'] = len(pack_img) - context['missing_img']

        complete_df = df[['name', 'calories', 'allergy']].merge(pack_img, left_on='name', right_index=True)
        complete_df['complete'] = (~complete_df['calories'].isnull()) & \
                                  (complete_df['pack images'] > 0) & complete_df['allergy']
        context['complete'] = complete_df['complete'].value_counts()[True]

        # Visualizations
        context['figure1'] = category_nutrient_distribution_plot(df)
        return context
