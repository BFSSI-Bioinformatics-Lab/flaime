from django.urls import path, re_path

from flaim.product_curator.views import IndexView

app_name = "product_curator"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
