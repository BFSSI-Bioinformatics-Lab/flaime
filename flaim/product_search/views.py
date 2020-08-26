from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from flaim.database.product_mappings import VALID_NUTRIENT_DICT


# Create your views here.
class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'product_search/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Used to populate the select HTML elements for DV filtering
        context['available_nutrients_dv'] = {k: v for k, v in VALID_NUTRIENT_DICT.items() if '_dv' in k}

        return context
