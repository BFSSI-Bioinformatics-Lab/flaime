import re

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
from django.db.models import F
from django.views.generic import TemplateView
from plotly.io import to_html
from urllib.parse import unquote

from flaim.database import models
from django.contrib.auth.mixins import LoginRequiredMixin


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class CategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/category_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'category' not in self.kwargs:
            context['category'] = 'Beverages'  # set default category TODO: set this to a random value instead
        else:
            context['category'] = unquote(
                self.kwargs['category'])  # pulls category from URL e.g. /reports/category/Beverages

        selection = context['category']

        plot_df = get_plot_df()
        plot_df = plot_df.loc[plot_df['category_text'] == selection]

        # Top bar
        context['report_title'] = selection
        context['product_count'] = plot_df.shape[0]
        context['calorie_median'] = f'{plot_df.calories.median():.0f}'
        context['sodium_median'] = f'{plot_df.sodium_dv.median()*100:.0f}%'
        context['fat_median'] = f'{plot_df.totalfat_dv.median()*100:.0f}%'
        context['sugar_median'] = f'{plot_df.sugar.median()*100:.0f}%'

        # Visualizations
        context['figure1'] = get_figure1(plot_df)
        return context


class BrandView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/store_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selection = 'WALMART'

        plot_df = get_plot_df()
        plot_df = plot_df.loc[plot_df['store'] == selection]

        # Top bar
        context['report_title'] = selection
        context['product_count'] = plot_df.shape[0]
        context['sodium_products_over_15'] = plot_df[plot_df.sodium_dv > 0.15].shape[0]
        context['fat_products_over_15'] = plot_df[plot_df.totalfat_dv > 0.15].shape[0]
        context['sugar_products_over_15'] = plot_df[plot_df.sugar > 0.15].shape[0]

        # Visualizations
        context['figure1'] = get_figure1(plot_df)
        return context


# Fetch dataset
def get_plot_df():
    products = models.Product
    nutrition_facts = models.NutritionFacts
    df1 = pd.DataFrame(list(products.objects
                            .annotate(category_text=F('predicted_category__predicted_category_1'))
                            .filter(most_recent=True)
                            .values()))
    df2 = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True).values()))
    df = df1.merge(df2, left_on='id', right_on='product_id')
    df['sugar'] /= 100
    df['brand'] = df['brand'].str.replace('’', "'")
    return df


# Figure generation
def get_figure1(df):
    nutrients = ['sodium_dv', 'totalfat_dv', 'sugar']
    fig = ff.create_distplot(df[nutrients].dropna().T.values,
                             nutrients, bin_size=.01)

    fig.update_layout(
        width=1100,
        xaxis_range=[0, 1],
        margin=dict(
            l=50,
            r=20,
            b=30,
            t=30,
        )
    )

    fig.add_shape(dict(
        type="line",
        yref='paper',
        x0=0.15,
        y0=0,
        x1=0.15,
        y1=1,
        line=dict(
            color="Red",
            width=2
        )))
    return to_html(fig, include_plotlyjs=False, full_html=False)
