import json
import logging
from flaim.database import models
from flaim.database.product_mappings import REFERENCE_CATEGORIES_CODING_DICT, REFERENCE_SUBCATEGORIES_CODING_DICT
from django.views.generic import ListView

logger = logging.getLogger(__name__)


class IndexView(ListView):
    model = models.Product
    template_name = 'product_curator/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Grab available categories and dump them context for use as a dropdown menu within datatables

        product_categories = [{'value': category, 'label': f'{key}: {category}'} for key, category in
                              REFERENCE_CATEGORIES_CODING_DICT.items()]

        product_subcategories = [{'value': subcategory, 'label': f'{key}: {subcategory}'} for key, subcategory in
                                 REFERENCE_SUBCATEGORIES_CODING_DICT.items()]
        context['product_categories'] = json.dumps(product_categories)
        context['product_subcategories'] = json.dumps(product_subcategories)
        context['user'] = self.request.user

        return context
