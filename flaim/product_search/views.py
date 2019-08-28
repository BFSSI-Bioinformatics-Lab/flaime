import json
from django.shortcuts import render
from django.views.generic import TemplateView

from flaim.database import models


# Create your views here.
class IndexView(TemplateView):
    template_name = 'product_search/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # TODO: Currently dynamically generates a list; this is very inefficient, but accurate.
        #  Better to keep a semi-regularly updated hardcoded list somewhere.
        brand_list = models.Product.objects.all()
        brand_list = list(set([x.brand for x in brand_list if x.brand is not None]))
        context['brand_json'] = json.dumps(brand_list)

        context['store_list'] = json.dumps(['LOBLAWS', 'WALMART', 'AMAZON'])

        return context
