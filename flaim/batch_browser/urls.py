from django.urls import path

from flaim.batch_browser.views import IndexView

app_name = "batch_browser"

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
