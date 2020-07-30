from django.views.generic import TemplateView


class DownloadView(TemplateView):
    template_name = 'data/download.html'


class QualityView(TemplateView):
    template_name = 'data/quality.html'
