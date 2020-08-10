from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class ProductView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class CategoryView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class BrandView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'


class StoreView(LoginRequiredMixin, TemplateView):
    template_name = 'reports_base.html'
