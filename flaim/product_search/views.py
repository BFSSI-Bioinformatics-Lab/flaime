import json
from django.shortcuts import render
from django.views.generic import TemplateView

from flaim.database import models


# Create your views here.
class IndexView(TemplateView):
    template_name = 'product_search/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
