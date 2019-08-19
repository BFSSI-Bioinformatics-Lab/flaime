import logging
from pathlib import Path
from django.conf import settings
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

        # Get image paths for the product
        images = list(Path(context['product'].loblaws_product.image_directory).glob("*"))
        images = [str(x).replace(settings.MEDIA_ROOT, settings.MEDIA_URL[:-1]) for x in images]
        context['product_images'] = images

        logger.debug(context)
        logger.debug(context['product_images'])

        return context
