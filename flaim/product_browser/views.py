import logging
from django.views.generic import TemplateView, DetailView
from flaim.database.models import Product

logger = logging.getLogger(__name__)


# Create your views here.
class IndexView(TemplateView):
    template_name = 'product_browser/index.html'


class ProductView(DetailView):
    model = Product
    template_name = 'product_browser/detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        logger.debug(f"product: {context}")
        logger.debug(context['product'].loblaws_product)
        return context


