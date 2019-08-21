from django.urls import path, re_path
from flaim.visualizer.views import IndexView


app_name = "visualizer"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
