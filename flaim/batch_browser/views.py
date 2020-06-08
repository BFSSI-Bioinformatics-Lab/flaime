import logging
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


# Create your views here.
class IndexView(TemplateView):
    template_name = 'batch_browser/index.html'
