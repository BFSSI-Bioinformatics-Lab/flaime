import json
from django.shortcuts import render
from django.views.generic import TemplateView

from flaim.database.nutrient_coding import VALID_NUTRIENT_DICT


# Create your views here.
class IndexView(TemplateView):
    template_name = 'product_search/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Used to populate the select HTML elements for DV filtering
        context['available_nutrients_dv'] = {k: v for k, v in VALID_NUTRIENT_DICT.items() if '_dv' in k}

        return context
