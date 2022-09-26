from django.urls import include, path
from rest_framework import routers
from flaim.database.api import views

router = routers.DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='products')
router.register(r'recent_products', views.RecentProductViewSet, basename='recent_products')
router.register(r'recent_products_test', views.RecentProductViewSetTest, basename='recent_products_test')
router.register(r'advanced_products', views.AdvancedProductViewSet, basename='advanced_products')
router.register(r'loblaws_products', views.LoblawsProductViewSet)
router.register(r'walmart_products', views.WalmartProductViewSet)
router.register(r'amazon_products', views.AmazonProductViewSet)
router.register(r'voila_products', views.VoilaProductViewSet)
router.register(r'grocerygateway_products', views.GroceryGatewayProductViewSet)
router.register(r'mintel_products', views.MintelProductViewSet)
router.register(r'nutrition_facts', views.NutritionFactsViewSet)

# Had to manually set the basename here because otherwise it tries to use the queryset as the basename
router.register(r'product_name', views.ProductNameViewSet, basename='product_name')
router.register(r'predicted_category_name', views.CategoryNameViewSet, basename='predicted_category_name')
router.register(r'predicted_subcategory_name', views.SubcategoryNameViewSet, basename='predicted_subcategory_name')
router.register(r'category', views.CategoryViewSet, basename='category')
router.register(r'subcategory', views.SubcategoryViewSet, basename='subcategory')
router.register(r'reference_category_support', views.ReferenceCategorySupportViewSet,
                basename='reference_category_support')
router.register(r'brand_name', views.BrandNameViewSet, basename='brand_name')
router.register(r'loblaws_breadcrumbs', views.LoblawsBreadcrumbViewSet, basename='loblaws_breadcrumbs')
router.register(r'product_images', views.ProductImageViewSet, basename='product_images')
router.register(r'front_of_pack', views.FrontOfPackLabelViewSet)
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'scrape_batches', views.ScrapeBatchViewSet, basename='scrape_batches')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('django-rq/', include('django_rq.urls'))
]
