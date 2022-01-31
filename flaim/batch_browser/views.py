import logging
from flaim.database import models
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

import os
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders

logger = logging.getLogger(__name__)


class IndexView(ListView):
    model = models.ScrapeBatch
    template_name = 'batch_browser/index.html'
    context_object_name = 'batches'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class BatchView(DetailView):
    model = models.ScrapeBatch
    template_name = 'batch_browser/batch_detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


def render_pdf_page(request, *args, **kwargs):
    scrapeBatch = models.ScrapeBatch
    template_path = 'batch_browser/pdf-view.html'
    context = {'scrapeBatch': scrapeBatch}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    # if download wanted:
    # response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # render pdf in page:
    response['Content-Disposition'] = 'filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

# def render_pdf_page(request):
#     scrapeBatch = models.ScrapeBatch
#     template_path = 'batch_browser/pdf-view.html'
#     context = {'scrapeBatch': scrapeBatch}
#     # Create a Django response object, and specify content_type as pdf
#     response = HttpResponse(content_type='application/pdf')
#     # if download wanted:
#     # response['Content-Disposition'] = 'attachment; filename="report.pdf"'
#     # render pdf in page:
#     response['Content-Disposition'] = 'filename="report.pdf"'
#     # find the template and render it.
#     template = get_template(template_path)
#     html = template.render(context)
#
#     # create a pdf
#     pisa_status = pisa.CreatePDF(
#         html, dest=response)
#     # if error then show some funny view
#     if pisa_status.err:
#         return HttpResponse('We had some errors <pre>' + html + '</pre>')
#     return response
