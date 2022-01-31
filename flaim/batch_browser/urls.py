from django.urls import path, re_path

from flaim.batch_browser.views import IndexView, BatchView
from flaim.batch_browser.views import render_pdf_page

app_name = "batch_browser"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    re_path("^(?P<pk>\d+)$", view=BatchView.as_view(), name="batch_view"),
    path('pdf/', render_pdf_page, name='test-pdf')
]
