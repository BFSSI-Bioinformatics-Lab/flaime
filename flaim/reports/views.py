from django.shortcuts import render
from django.views.generic import TemplateView


class ProductView(TemplateView):
    template_name = 'reports/product_report.html'


class NutrientView(TemplateView):
    template_name = 'reports_base.html'


class CategoryView(TemplateView):
    template_name = 'reports_base.html'


class BrandView(TemplateView):
    template_name = 'reports_base.html'


class StoreView(TemplateView):
    template_name = 'reports_base.html'
