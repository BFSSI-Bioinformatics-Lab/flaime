from textwrap import wrap
from urllib.parse import unquote

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.views.generic import TemplateView
from plotly.io import to_html

from flaim.database import models


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class CategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/category_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plot_df = get_plot_df()

        if 'category' not in self.kwargs:
            context['category'] = np.random.choice(plot_df['category_text'].unique())  # set default category
        else:
            # pulls category from URL e.g. /reports/category/Beverages
            context['category'] = unquote(self.kwargs['category'])

        plot_df = plot_df.loc[plot_df['category_text'] == context['category']]

        # Top bar
        context['image'] = context['category'].lower()
        context['product_count'] = plot_df.shape[0]
        context['calorie_median'] = f'{plot_df.calories.median():.0f}'

        context['sodium_color'] = get_nutrient_color(plot_df.sodium_dv.median())
        context['sodium_median'] = f'{plot_df.sodium_dv.median() * 100:.0f}%'

        context['fat_color'] = get_nutrient_color(plot_df.totalfat_dv.median())
        context['fat_median'] = f'{plot_df.totalfat_dv.median() * 100:.0f}%'

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
        plot_df = get_plot_df()

        if 'store' not in self.kwargs:
            context['store'] = np.random.choice(plot_df['store'].unique())  # set default category
        else:
            context['store'] = unquote(
                self.kwargs['store'].upper())  # pulls category from URL e.g. /reports/store/Loblaws

        plot_df = plot_df.loc[plot_df['store'] == context['store']]

        # Top bar
        context['image'] = context['store'].lower()
        context['store'] = context['store'].capitalize()
        context['product_count'] = plot_df.shape[0]
        context['sodium_products_over_15'] = plot_df[plot_df.sodium_dv > 0.15].shape[0]
        context['fat_products_over_15'] = plot_df[plot_df.totalfat_dv > 0.15].shape[0]
        context['sugar_products_over_15'] = plot_df[plot_df.sugar > 0.15].shape[0]

        # Visualizations
        context['figure1'] = get_category_nutrient_distribution_plot(plot_df)
        return context


def get_nutrient_color(value):
    return 'text-success' if value <= 0.15 else 'text-danger'


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
def get_nutrient_distribution_plot(df):
    nutrients = ['sodium_dv', 'totalfat_dv', 'sugar']
    fig = ff.create_distplot(df[nutrients].dropna().T.values, nutrients, bin_size=.01)

    fig.update_layout(
        width=1100,
        xaxis_range=[0, min([1, max(df[n].quantile(0.95) for n in nutrients)])],
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


def get_category_nutrient_distribution_plot(df):
    def over_15(row):
        return 1 if row > 0.15 else 0

    nutrients = ['sodium_dv', 'totalfat_dv', 'sugar']
    categories = ['Beverages', 'Cereals and Other Grain Products', 'Dairy Products and Substitutes',
                  'Meat and Poultry, Products and Substitutes', 'Snacks']

    category_labels = ['<br>'.join(wrap(c, 20)) for c in categories]

    plot_df = df.loc[df['category_text'].isin(categories)]

    for n in nutrients:
        plot_df[f'{n}_count'] = plot_df[n].apply(lambda row: over_15(row))

    plot_df = plot_df[['category_text'] + [f'{n}_count' for n in nutrients]].groupby(
        'category_text').sum().reindex(categories)

    data = [
        go.Bar(name=nutrient, x=category_labels, y=plot_df[f'{nutrient}_count']) for nutrient in nutrients
    ]

    layout = dict(
        width=1100,
        margin=dict(
            l=50,
            r=20,
            b=20,
            t=30,
        ),
        xaxis=dict(
            showgrid=True,
            tickson='boundaries',
            tickangle=0,
        ),
    )

    fig = go.Figure(data=data, layout=layout)

    return to_html(fig, include_plotlyjs=False, full_html=False)
