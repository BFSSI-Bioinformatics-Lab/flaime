from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'frontend/index.html'


# def index(request):
#     return render(request, 'frontend/index.html')
