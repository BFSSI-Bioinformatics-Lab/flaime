import logging
import rest_framework_datatables

from django.contrib.auth.models import Group

from rest_framework import viewsets, filters
from django_filters import rest_framework as df_filters
from django.db.models import Q
from flaim.database import models
from flaim.database import serializers
from django.contrib.auth import get_user_model

from rest_framework.pagination import PageNumberPagination

User = get_user_model()

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 20


# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    # pagination_class = StandardResultsSetPagination
    queryset = models.Product.objects.all().order_by('-created')
    serializer_class = serializers.ProductSerializer
    filter_backends = [df_filters.DjangoFilterBackend,
                       rest_framework_datatables.filters.DatatablesFilterBackend,
                       filters.SearchFilter
                       ]
    filterset_fields = ('name', 'store', 'product_code', 'brand')
    search_fields = ['name', 'store', 'brand']


class NutritionFactsViewSet(viewsets.ModelViewSet):
    queryset = models.NutritionFacts.objects.all().order_by('-created')
    serializer_class = serializers.NutritionFactsSerializer

    def get_queryset(self):
        query_params = self.request.query_params

        # Check for ?ingredients_contains={ingredient} parameter, and filter results if necessary
        ingredients_contains = query_params.get('ingredients_contains', None)
        if ingredients_contains:
            queryset = models.NutritionFacts.objects.filter(ingredients__icontains=ingredients_contains).order_by('-id')
            return queryset

        # Return everything by default
        queryset = models.NutritionFacts.objects.all().order_by('-id')
        return queryset


class AdvancedProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.AdvancedProductSerializer

    def get_queryset(self):
        query_params = self.request.query_params
        #
        # # Check for ?ingredients_contains={ingredient} parameter, and filter results if necessary
        ingredients_contains = query_params.get('ingredients_contains', None)
        name_contains = query_params.get('name_contains', None)
        queryset = models.Product.objects.all()

        if ingredients_contains:
            print('Searching ingredients')
            queryset = queryset.filter(nutrition_facts__ingredients__icontains=ingredients_contains)
        if name_contains:
            print('Searching names')
            queryset = queryset.filter(name__icontains=name_contains)

        # # Return everything by default
        return queryset.order_by('-id')


class LoblawsProductViewSet(viewsets.ModelViewSet):
    queryset = models.LoblawsProduct.objects.all().order_by('-created')
    serializer_class = serializers.LoblawsProductSerializer


class WalmartProductViewSet(viewsets.ModelViewSet):
    queryset = models.WalmartProduct.objects.all().order_by('-created')
    serializer_class = serializers.WalmartProductSerializer


class AmazonProductViewSet(viewsets.ModelViewSet):
    queryset = models.AmazonProduct.objects.all().order_by('-created')
    serializer_class = serializers.AmazonProductSerializer


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = models.ProductImage.objects.all().order_by('-created')
    serializer_class = serializers.ProductImageSerializer


class FrontOfPackLabelViewSet(viewsets.ModelViewSet):
    queryset = models.FrontOfPackLabel.objects.all().order_by('-created')
    serializer_class = serializers.FrontOfPackLabelSerializer

    filter_backends = [df_filters.DjangoFilterBackend]
    filterset_fields = ('id', 'product_image', 'label_detected',)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('-name')
    serializer_class = serializers.GroupSerializer
