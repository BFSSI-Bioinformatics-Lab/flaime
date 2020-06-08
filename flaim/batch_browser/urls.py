from django.urls import path

from flaim.batch_browser.views import IndexView

app_name = "product_browser"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
