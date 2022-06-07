from django.urls import path, re_path

from flaim.reports.views import ProductView, NutrientView, CategoryView, BrandView, StoreView, SubcategoryView

app_name = "reports"

urlpatterns = [
    path("builder/", ProductView.as_view(), name='product_report_builder'),
    path("nutrient/", NutrientView.as_view(), name='nutrient_report'),
    path("subcategory/", SubcategoryView.as_view(), name='subcategory_report'),
    re_path(r"^subcategory/(?P<subcategory>[\w|\W]+)/$", SubcategoryView.as_view(), name='subcategory_report'),
    path("category/", CategoryView.as_view(), name='category_report'),
    re_path(r"^category/(?P<category>[\w|\W]+)/$", CategoryView.as_view(), name='category_report'),
    path("brand/", BrandView.as_view(), name='brand_report'),
    path("store/", StoreView.as_view(), name='store_report'),
    re_path(r"^store/(?P<store>[\w|\W]+)/$", StoreView.as_view(), name='store_report'),
]
