from django.views.generic import ListView, View
from flaim.database import models, nutrient_coding

import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
import json

from django.core import serializers
from flaim.database.api.serializers import ProductSerializer


# def index(request):
#     x_data = [0, 1, 2, 3]
#     y_data = [x ** 2 for x in x_data]
#     plot_div = plot([Scatter(x=x_data, y=y_data,
#                              mode='lines', name='test',
#                              opacity=0.8, marker_color='green')],
#                     output_type='div', include_plotlyjs=False)
#     return render(request, template_name='index.html', context={'plot_div': plot_div})


# Create your views here.
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
        fig.add_trace(go.Box(x=df['sodium_dv'].dropna(), name='Sodium'))
        fig.add_trace(go.Box(x=df['totalfat_dv'].dropna(), name='Total Fat'))
        fig.add_trace(go.Box(x=df['sugar'].dropna() / 100, name='Sugar'))

        fig.update_layout(barmode='stack')
        fig.update_traces(opacity=0.75)

        fig['layout']['xaxis'].update(range=[0, 1])

        plot_div = to_html(fig, include_plotlyjs=False, full_html=False)
        context['plot_div'] = plot_div
        return context




class LoblawsBreadcrumbView(View):
    """ Should calculate the data needed for the treemap on the server and store it to serve the end JSON to
     the user to prevent unnecessary delay """
    pass
