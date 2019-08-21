from django.views.generic import ListView
from flaim.database import models, nutrient_coding
import json

from django.core import serializers
from flaim.database.serializers import ProductSerializer


# Create your views here.
class IndexView(ListView):
    model = models.Product
    template_name = 'visualizer/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Example code on how to get all of the distinct values from a column in a table
        subcategory_list = self.model.objects.values_list('loblaws_product__subcategory').distinct()
        subcategory_list = [x[0] for x in subcategory_list if x[0] is not None]
        context['subcategory_list'] = json.dumps(subcategory_list)

        nutrient_list = nutrient_coding.EXPECTED_NUTRIENTS
        context['nutrient_list'] = json.dumps(nutrient_list)

        # Serializing a queryset with only fields of interest
        # json_query = serializers.serialize("json", self.model.objects.all())
        # context['json_query'] = json_query

        return context
