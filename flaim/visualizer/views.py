from django.views.generic import ListView, View
from flaim.database import models

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html


class IndexView(ListView):
    model = models.Product
    nutrition_facts = models.NutritionFacts
    template_name = 'visualizer/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        df = pd.DataFrame(list(self.nutrition_facts.objects.filter(product__most_recent=True).values()))
        # df1.to_csv('nutrition_facts.csv', index=False)
        # df2 = pd.DataFrame(list(self.model.objects.filter(most_recent=True).values()))
        # df2.to_csv('products.csv', index=False)
        # print(df.columns)

        fig = go.Figure()
        fig.add_trace(go.Box(x=df['sodium_dv'].dropna()*100, name='Sodium', boxmean=True))
        fig.add_trace(go.Box(x=df['totalfat_dv'].dropna()*100, name='Total Fat', boxmean=True))
        fig.add_trace(go.Box(x=df['sugar'].dropna(), name='Sugar', boxmean=True))

        fig.update_layout(barmode='stack')
        fig.update_traces(opacity=0.75)

        fig['layout']['xaxis'].update(range=[0, 100])
        fig.update_layout(
            xaxis_title="Daily Value (%)",
            title={
                'text': 'Distribution of Daily Values for Select Nutrients',
                'y': 0.9,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'})

        plot_div = to_html(fig, include_plotlyjs=False, full_html=False)
        context['plot_div'] = plot_div
        return context


class LoblawsBreadcrumbView(View):
    """ Should calculate the data needed for the treemap on the server and store it to serve the end JSON to
     the user to prevent unnecessary delay """
    pass
