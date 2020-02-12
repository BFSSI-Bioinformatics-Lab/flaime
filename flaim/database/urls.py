from django.urls import include, path
from rest_framework import routers
from flaim.database import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'loblaws_products', views.LoblawsProductViewSet)
router.register(r'walmart_products', views.WalmartProductViewSet)
router.register(r'amazon_products', views.AmazonProductViewSet)
router.register(r'nutrition_facts', views.NutritionFactsViewSet)

# Had to manually set the basename here because otherwise it tries to use the queryset as the basename
router.register(r'advanced_product', views.AdvancedProductViewSet, basename='advanced_product')
router.register(r'product_images', views.ProductImageViewSet)
router.register(r'front_of_pack', views.FrontOfPackLabelViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('django-rq/', include('django_rq.urls'))
]
