import re
from urllib.parse import unquote

import numpy as np
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from flaim.database.product_mappings import PRODUCT_STORES, REFERENCE_CATEGORIES_DICT, \
    REFERENCE_SUBCATEGORIES_CODING_DICT
from flaim.reports.data import ReportData, StoreReportData
from flaim.reports.plots import nutrient_distribution_plot, category_nutrient_distribution_plot
from flaim.reports.util import nutrient_color, rank_suffix, build_top_x_sentence, make_list, \
    build_top_ingredient_sentence


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


def category_context_builder(df: pd.DataFrame, context: dict):
    ingredient_count = df['ingredients'].str.findall(',').fillna('').apply(lambda row: len(row) + 1)
    context['ingredient_q25'] = int(ingredient_count.quantile(0.25))
    context['ingredient_q75'] = int(ingredient_count.quantile(0.75))
    context['common_ingredients'] = build_top_ingredient_sentence(df['ingredients'])
    atwater_results = df.atwater_result.value_counts().to_dict()
    if 'Within Threshold' not in atwater_results:
        atwater_results['Within Threshold'] = 0
    context['atwater_pass'] = atwater_results['Within Threshold']
    if 'Investigation Required' not in atwater_results:
        atwater_results['Investigation Required'] = 0
    context['atwater_fail'] = atwater_results['Investigation Required']
    if 'Missing Information' not in atwater_results:
        atwater_results['Missing Information'] = 0
    context['atwater_missing'] = atwater_results['Missing Information']

    # Top bar
    context['image'] = context['category'].lower()
    context['product_count'] = df.shape[0]
    context['store_count'] = df['store'].nunique()
    context['manual_category_count'] = df['manual_category_text'].dropna().shape[0]
    context['predicted_category_count'] = context['product_count'] - context['manual_category_count']

    context['calorie_median'] = f'{df.calories.fillna(0).median():.0f}'

    context['sodium_color'] = nutrient_color(df.sodium_dv.median())
    context['sodium_median'] = f'{df.sodium_dv.fillna(0).median() * 100:.0f}%'

    context['fat_color'] = nutrient_color(df.saturatedfat_dv.median())
    context['fat_median'] = f'{df.saturatedfat_dv.fillna(0).median() * 100:.0f}%'

    context['sugar_color'] = nutrient_color(df.sugar.median())
    context['sugar_median'] = f'{df.sugar.fillna(0).median() * 100:.0f}%'

    # Visualizations
    context['figure1'] = nutrient_distribution_plot(df)
    return


class SubcategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/subcategory_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = ReportData()
        df = data.df.copy()  # temp copy

        context['subcategory'] = self.kwargs['subcategory']
        # Figure out parent category for image display
        for category, subcategories in REFERENCE_CATEGORIES_DICT.items():
            if self.kwargs['subcategory'] in subcategories:
                context['category'] = category
                context['image'] = category.lower()
        subcategories = list(
            set(REFERENCE_SUBCATEGORIES_CODING_DICT.values()).intersection(set(df['subcategory_text'].unique())))
        subcategories.sort()
        context['subcategories'] = subcategories

        df = df.loc[df['category_text'] == context['category']]

        context['category_count'] = df['subcategory_text'].nunique()
        medians = df.groupby('subcategory_text').median()

        context['sodium_rank'] = rank_suffix(medians.sort_values(by='sodium_dv', ascending=False)
                                             .index.get_loc(context['subcategory']))
        context['fat_rank'] = rank_suffix(medians.sort_values(by='saturatedfat_dv', ascending=False)
                                          .index.get_loc(context['subcategory']))
        context['sugar_rank'] = rank_suffix(medians.sort_values(by='sugar', ascending=False)
                                            .index.get_loc(context['subcategory']))

        df = df.loc[df['subcategory_text'] == context['subcategory']]
        category_context_builder(df, context)
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

        context['sodium_rank'] = rank_suffix(medians.sort_values(by='sodium_dv', ascending=False)
                                             .index.get_loc(context['category']))
        context['fat_rank'] = rank_suffix(medians.sort_values(by='saturatedfat_dv', ascending=False)
                                          .index.get_loc(context['category']))
        context['sugar_rank'] = rank_suffix(medians.sort_values(by='sugar', ascending=False)
                                            .index.get_loc(context['category']))

        df = df.loc[df['category_text'] == context['category']]
        category_context_builder(df, context)
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

        context['common_categories'] = build_top_x_sentence(df['category_text'], 3)
        context['common_brands'] = build_top_x_sentence(df['brand'], 5)
        atwater_results = df.atwater_result.value_counts().to_dict()
        if 'Within Threshold' not in atwater_results:
            atwater_results['Within Threshold'] = 0
        context['atwater_pass'] = atwater_results['Within Threshold']
        if 'Investigation Required' not in atwater_results:
            atwater_results['Investigation Required'] = 0
        context['atwater_fail'] = atwater_results['Investigation Required']
        if 'Missing Information' not in atwater_results:
            atwater_results['Missing Information'] = 0
        context['atwater_missing'] = atwater_results['Missing Information']

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

        agg_df = pivot_df.groupby('name').agg({c: lambda x: make_list(x) for c in pivot_columns})
        if 'other' in agg_df:
            if 'none' in agg_df:
                agg_df['none'] = agg_df['none'] + agg_df['other']
            else:
                agg_df['none'] = agg_df['other'].copy()
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

        if context['store'] == 'Mintel':
            complete_df['complete'] = (~complete_df['calories'].isnull()) & complete_df['allergy']
        else:
            complete_df['complete'] = (~complete_df['calories'].isnull()) & \
                                      (complete_df['pack images'] > 0) & complete_df['allergy']
        context['complete'] = complete_df['complete'].value_counts()[True]

        # Visualizations
        context['figure1'] = category_nutrient_distribution_plot(df)
        return context
