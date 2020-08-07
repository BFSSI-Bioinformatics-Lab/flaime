import re

import numpy as np
import pandas as pd
import plotly.figure_factory as ff
from django.views.generic import TemplateView
from plotly.io import to_html

from flaim.database import models


class ProductView(TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(TemplateView):
    template_name = 'reports_base.html'


class CategoryView(TemplateView):
    model = models.Product
    nutrition_facts = models.NutritionFacts
    template_name = 'reports/category_report.html'

    @staticmethod
    def get_figure1(df):
        nutrients = ['sodium_dv', 'totalfat_dv', 'sugar']
        plot_df = df.loc[df['breadcrumbs_last'].str.contains('soup', flags=re.IGNORECASE) == True].copy()
        plot_df['sugar'] /= 100

        fig = ff.create_distplot(plot_df[nutrients].dropna().T.values,
                                 nutrients, bin_size=.01)

        fig.update_layout(
            width=1100,
            xaxis_range=[0,0.6],
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        df1 = pd.DataFrame(list(self.model.objects.filter(most_recent=True).values()))

        def last_crumb(breadcrumbs):
            return breadcrumbs[-1] if breadcrumbs and len(breadcrumbs) > 0 else np.nan
        df1['breadcrumbs_last'] = df1['breadcrumbs_array'].apply(lambda row: last_crumb(row))

        df2 = pd.DataFrame(list(self.nutrition_facts.objects.filter(product__most_recent=True).values()))

        df = df1.merge(df2, left_on='id', right_on='product_id')

        context['figure1'] = CategoryView.get_figure1(df)
        return context


class BrandView(TemplateView):
    template_name = 'reports_base.html'


class StoreView(TemplateView):
    template_name = 'reports_base.html'
