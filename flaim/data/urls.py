from django.urls import path

from flaim.data.views import QualityView, DownloadView

app_name = "data"

urlpatterns = [
    path("download/", DownloadView.as_view(), name='data_download'),
    path("quality/", QualityView.as_view(), name='data_quality'),
]
