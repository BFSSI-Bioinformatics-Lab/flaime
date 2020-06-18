from django.views.generic import ListView, View
from flaim.database import models, nutrient_coding

import pandas as pd
from plotly.offline import plot
from plotly.graph_objs import Scatter
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
    model = models.NutritionFacts
    template_name = 'visualizer/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        df = pd.DataFrame(list(self.model.objects.filter(product__most_recent=True).prefetch_related('product').values()))
        print(df.columns)

        x_data = [0, 1, 2, 3]
        y_data = [x ** 2 for x in x_data]
        plot_div = plot([Scatter(x=x_data, y=y_data,
                                 mode='lines', name='test',
                                 opacity=0.8, marker_color='green')],
                        output_type='div', include_plotlyjs=True)
        context['plot_div'] = plot_div
        return context




class LoblawsBreadcrumbView(View):
    """ Should calculate the data needed for the treemap on the server and store it to serve the end JSON to
     the user to prevent unnecessary delay """
    pass
