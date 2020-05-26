from django.views.generic import ListView, View
from flaim.database import models, nutrient_coding
import json

from django.core import serializers
from flaim.database.api.serializers import ProductSerializer


# Create your views here.
class IndexView(ListView):
    model = models.Product
    template_name = 'visualizer/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class LoblawsBreadcrumbView(View):
    """ Should calculate the data needed for the treemap on the server and store it to serve the end JSON to
     the user to prevent unnecessary delay """
    pass
