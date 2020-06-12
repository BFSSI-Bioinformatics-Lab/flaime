import logging
from flaim.database import models
from django.views.generic import ListView

logger = logging.getLogger(__name__)


class IndexView(ListView):
    model = models.ScrapeBatch
    template_name = 'batch_browser/index.html'
    context_object_name = 'batches'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
