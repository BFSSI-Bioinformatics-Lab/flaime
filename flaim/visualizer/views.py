import ast

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from django.views.generic import ListView, View
from plotly.io import to_html

from flaim.database import models


class IndexView(ListView):
    model = models.Product
    nutrition_facts = models.NutritionFacts
    template_name = 'visualizer/index.html'
    context_object_name = 'products'

    @staticmethod
    def get_figure1(df):
        fig = go.Figure()
        fig.add_trace(go.Box(x=df['sodium_dv'].dropna() * 100, name='Sodium', boxmean=True))
        fig.add_trace(go.Box(x=df['totalfat_dv'].dropna() * 100, name='Total Fat', boxmean=True))
        fig.add_trace(go.Box(x=df['sugar'].dropna(), name='Sugar', boxmean=True))

        fig.update_layout(barmode='stack')
        fig.update_traces(opacity=0.75)

        fig['layout']['xaxis'].update(range=[0, 100])
        fig.update_layout(
            xaxis_title="Daily Value (%)",
            margin=dict(
                l=0,
                r=0,
                b=50,
                t=50,
            ),
            title={
                'text': 'Distribution of Select Nutrients (Stores Combined)',
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
            height=400)
        return to_html(fig, include_plotlyjs=False, full_html=False)

    @staticmethod
    def get_figure2(df):
        data = [go.Box(y=df['store'], x=df['sodium_dv'] * 100, name='Sodium', boxmean=True, orientation='h'),
                go.Box(y=df['store'], x=df['totalfat_dv'] * 100, name='Total Fat', boxmean=True, orientation='h'),
                go.Box(y=df['store'], x=df['sugar'], name='Sugar', boxmean=True, orientation='h')]

        update_menus = list([
            dict(active=0,
                 buttons=list([
                     dict(label='All',
                          method='update',
                          args=[{'visible': [True, True, True]},
                                {'title': 'Distribution of Select Nutrients by Store'}]),
                     dict(label='Sodium',
                          method='update',
                          args=[{'visible': [True, False, False]},
                                {'title': 'Distribution of Sodium by Store'}]),
                     dict(label='Total Fat',
                          method='update',
                          args=[{'visible': [False, True, False]},
                                {'title': 'Distribution of Total Fat by Store'}]),
                     dict(label='Sugar',
                          method='update',
                          args=[{'visible': [False, False, True]},
                                {'title': 'Distribution of Sugar by Store'}])
                 ]),
                 )
        ])

        layout = dict(
            title={
                'text': 'Distribution of Select Nutrients by Store',
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
            margin=dict(
                l=0,
                r=0,
                b=50,
                t=50,
            ),
            updatemenus=update_menus, showlegend=True,
            xaxis_title='Daily Value (%)',
            boxmode='group',
            height=400,
            xaxis_range=[0, 100])

        fig = go.Figure(data=data, layout=layout)
        return to_html(fig, include_plotlyjs=False, full_html=False)

    @staticmethod
    def get_figure3(df):
        plot_df = df.copy()
        top_breadcrumbs = list(plot_df['breadcrumbs_last'].value_counts().head(21).index)
        if '' in top_breadcrumbs:
            top_breadcrumbs.remove('')
        else:
            top_breadcrumbs = top_breadcrumbs[:-1]
        plot_df = plot_df[plot_df['breadcrumbs_last'].isin(top_breadcrumbs)]

        data = [go.Box(x=plot_df['breadcrumbs_last'], y=plot_df['sodium_dv'] * 100, name='Sodium', boxmean=True),
                go.Box(x=plot_df['breadcrumbs_last'], y=plot_df['totalfat_dv'] * 100, name='Total Fat', boxmean=True),
                go.Box(x=plot_df['breadcrumbs_last'], y=plot_df['sugar'], name='Sugar', boxmean=True)]

        update_menus = list([
            dict(active=0,
                 buttons=list([
                     dict(label='All',
                          method='update',
                          args=[{'visible': [True, True, True]},
                                {'title': 'Distribution of Select Nutrients by Category (Top 20 Breadcrumbs)'}]),
                     dict(label='Sodium',
                          method='update',
                          args=[{'visible': [True, False, False]},
                                {'title': 'Distribution of Sodium by Category (Top 20 Breadcrumbs)'}]),
                     dict(label='Total Fat',
                          method='update',
                          args=[{'visible': [False, True, False]},
                                {'title': 'Distribution of Total Fat by Category (Top 20 Breadcrumbs)'}]),
                     dict(label='Sugar',
                          method='update',
                          args=[{'visible': [False, False, True]},
                                {'title': 'Distribution of Sugar by Category (Top 20 Breadcrumbs)'}])
                 ]),
                 )
        ])

        layout = dict(title={
            'text': 'Distribution of Select Nutrients by Category (Top 20 Breadcrumbs)',
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
            updatemenus=update_menus, showlegend=True,
            yaxis_title='Daily Value (%)',
            boxmode='group',
            width=1400,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=50,
            ),
            yaxis_range=[0, 100])

        fig = go.Figure(data=data, layout=layout)

        return to_html(fig, include_plotlyjs=False, full_html=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        df1 = pd.DataFrame(list(self.model.objects.filter(most_recent=True).values()))
        # df1['breadcrumbs_array'] = df1['breadcrumbs_array'].apply(lambda row: list(filter(None, ast.literal_eval(row))))

        def last_crumb(breadcrumbs):
            return breadcrumbs[-1] if breadcrumbs and len(breadcrumbs) > 0 else np.nan
        df1['breadcrumbs_last'] = df1['breadcrumbs_array'].apply(lambda row: last_crumb(row))

        df2 = pd.DataFrame(list(self.nutrition_facts.objects.filter(product__most_recent=True).values()))

        df = df1.merge(df2, left_on='id', right_on='product_id')

        context['figure1'] = IndexView.get_figure1(df)
        context['figure2'] = IndexView.get_figure2(df)
        context['figure3'] = IndexView.get_figure3(df)
        return context


class LoblawsBreadcrumbView(View):
    """ Should calculate the data needed for the treemap on the server and store it to serve the end JSON to
     the user to prevent unnecessary delay """
    pass
