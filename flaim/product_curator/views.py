import json
import logging
from flaim.database import models
from flaim.database.product_mappings import PRODUCT_CATEGORIES
from django.views.generic import ListView

logger = logging.getLogger(__name__)


class IndexView(ListView):
    model = models.Product
    template_name = 'product_curator/index.html'
    context_object_name = 'products'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Grab available categories and dump them context for use as a dropdown menu within datatables
        product_categories = []
        for i, category in enumerate(PRODUCT_CATEGORIES):
            product_categories.append({
                'value': i,
                'label': category
            })
        context['product_categories'] = json.dumps(product_categories)
        print(context['product_categories'])

        return context
