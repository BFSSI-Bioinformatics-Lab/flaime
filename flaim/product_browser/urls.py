from django.urls import path, re_path

from flaim.product_browser.views import IndexView, ProductView, ProductUpdateView

app_name = "product_browser"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    re_path("^(?P<pk>\d+)$", view=ProductView.as_view(), name="product_view"),
    re_path("^(?P<pk>\d+)/update/$", view=ProductUpdateView.as_view(), name="update_view")
]
