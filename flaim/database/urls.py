from django.urls import include, path
from rest_framework import routers
from flaim.database import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'nutrition_facts', views.NutritionFactsViewSet)
router.register(r'loblaws_products', views.LoblawsProductViewSet)
router.register(r'walmart_products', views.WalmartProductViewSet)
router.register(r'amazon_products', views.AmazonProductViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('django-rq/', include('django_rq.urls'))
]