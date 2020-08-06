from django.urls import include, path
from flaim.visualizer.api import views
from rest_framework import routers

app_name = "visualizer"

router = routers.DefaultRouter()
router.register(r'test', views.Test, basename='test')

urlpatterns = [
    path('', include(router.urls)),
]
