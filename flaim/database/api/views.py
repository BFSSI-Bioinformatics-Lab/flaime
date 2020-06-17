import logging
import rest_framework_datatables

from django.contrib.auth.models import Group

from rest_framework import viewsets, filters
from django_filters import rest_framework as df_filters
from django.utils.dateparse import parse_date
from flaim.database import models
from flaim.database.api import serializers
from django.contrib.auth import get_user_model
from flaim.database.nutrient_coding import VALID_NUTRIENT_COLUMNS
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

User = get_user_model()

logger = logging.getLogger(__name__)


class Select2PaginationClass(PageNumberPagination):
    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'results': data
        })


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 20


# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    """
    Returns all products within the database, while offering various filtering options.

    ## Batch filtering

    - Scrape batches can be filtered by ID through the batch_id keyword, e.g. `?batch_id=1`

    ## Date filtering

    - Dates can be filtered by providing start_date and end_date params in YYYY-MM-DD format, e.g. `?start_date=1991-01-01&end_date=2000-01-01`

    """
    # pagination_class = StandardResultsSetPagination
    serializer_class = serializers.ProductSerializer
    filter_backends = [df_filters.DjangoFilterBackend,
                       rest_framework_datatables.filters.DatatablesFilterBackend,
                       filters.SearchFilter
                       ]

    filterset_fields = ('name', 'store', 'product_code', 'brand')
    search_fields = ['name', 'store', 'brand']

    def get_queryset(self):
        queryset = models.Product.objects.all().order_by('-created')
        queryset = queryset.prefetch_related('nutrition_facts')

        # Batch Filtering
        batch_id = self.request.query_params.get('batch_id', None)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)

        # Date Filtering
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date and end_date:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            queryset = queryset.filter(batch__scrape_date__gte=start_date, batch__scrape_date__lte=end_date)

        return queryset


# Create your views here.
class RecentProductViewSet(viewsets.ModelViewSet):
    # pagination_class = StandardResultsSetPagination
    queryset = models.Product.objects.filter(most_recent=True).order_by('-created')
    serializer_class = serializers.RecentProductSerializer
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
        brand_contains = query_params.get('brand_contains', None)
        # description_contains = query_params.get('description_contains', None)  # TODO: Currently stored in loblaws model, but should be moved to product
        queryset = models.Product.objects.all()

        # print(query_params)
        valid_dv_nutrients = [x for x in VALID_NUTRIENT_COLUMNS if '_dv' in x]
        for nutrient in valid_dv_nutrients:
            if nutrient in dict(query_params):
                min_, max_ = dict(query_params)[nutrient][0].split(',')
                if min_ == 0 and max_ == 1:
                    break
                filter_ = f'nutrition_facts__{nutrient}__range'
                print(filter_)
                queryset = queryset.filter(**{filter_: (min_, max_)})
                # print(f'{n}: {min_} - {max_}')

        if ingredients_contains:
            ingredients = ingredients_contains.split(',')
            for i in ingredients:
                queryset = queryset.filter(nutrition_facts__ingredients__icontains=i)
        if name_contains:
            queryset = queryset.filter(name__icontains=name_contains)
        if brand_contains:
            queryset = queryset.filter(brand__icontains=brand_contains)
        # if description_contains:
        #     queryset = queryset.filter(loblaws_product__description__icontains=description_contains)

        # # Return everything by default
        return queryset.order_by('-id')


class ProductNameViewSet(viewsets.ModelViewSet):
    pagination_class = Select2PaginationClass
    serializer_class = serializers.ProductNameSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search', None)
        if search is not None:
            return models.Product.objects.filter(name__icontains=search)
        else:
            return models.Product.objects.all()


class BrandNameViewSet(viewsets.ModelViewSet):
    pagination_class = Select2PaginationClass
    serializer_class = serializers.BrandNameSerializer

    def get_queryset(self):
        search = self.request.query_params.get('search', None)
        if search is not None:
            return models.Product.objects.filter(brand__icontains=search)
        else:
            return models.Product.objects.all()


class ScrapeBatchViewSet(viewsets.ModelViewSet):
    queryset = models.ScrapeBatch.objects.all().order_by('-created')
    serializer_class = serializers.ScrapeBatchSerializer


class LoblawsProductViewSet(viewsets.ModelViewSet):
    queryset = models.LoblawsProduct.objects.all().order_by('-created')
    serializer_class = serializers.LoblawsProductSerializer


class LoblawsBreadcrumbViewSet(viewsets.ModelViewSet):
    pagination_class = None
    queryset = models.LoblawsProduct.objects.all().order_by('-created')
    serializer_class = serializers.LoblawsBreadcrumbSerializer


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
