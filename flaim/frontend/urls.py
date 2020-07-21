from django.views.generic import TemplateView
from django.urls import path, re_path
from . import views

app_name = "frontend"

urlpatterns = [
    re_path('^.*$', TemplateView.as_view(template_name='frontend/index.html'))  # allow any URL after frontend
]
