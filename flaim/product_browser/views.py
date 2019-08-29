import logging
from pathlib import Path
from django.conf import settings
from django.views.generic import TemplateView, DetailView
from flaim.database.models import Product, ProductImage, FrontOfPackLabel

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

        # Get image paths for the product. This is pretty gross and should be refactored. TODO: Make this not terrible
        images = list(Path(context['product'].loblaws_product.image_directory).glob("*"))
        images = [x for x in images if x.is_file()]
        images_formatted = [str(x).replace(settings.MEDIA_ROOT, settings.MEDIA_URL[:-1]) for x in images]
        context['product_images'] = images_formatted

        # Images
        product_image_objects = ProductImage.objects.filter(product=context['product'])
        context['product_image_objects'] = product_image_objects

        # FOP
        fop_objects = FrontOfPackLabel.objects.filter(product_image__in=product_image_objects)
        context['fop_objects'] = fop_objects

        logger.debug(context)
        logger.debug(context['product_images'])

        return context
