from django.contrib.auth.models import Group
from flaim.database import models
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class EagerLoadingMixin:
    @classmethod
    def setup_eager_loading(cls, queryset):
        if hasattr(cls, "_SELECT_RELATED_FIELDS"):
            queryset = queryset.select_related(*cls._SELECT_RELATED_FIELDS)  # One-to-One
        if hasattr(cls, "_PREFETCH_RELATED_FIELDS"):
            queryset = queryset.prefetch_related(*cls._PREFETCH_RELATED_FIELDS)  # Many-to-Many or reverse foreign keys
        return queryset


class ScrapeBatchSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.ScrapeBatch
        fields = '__all__'


class LoblawsProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.LoblawsProduct
        fields = (
            'id', 'url', 'upc_list'
        )


class WalmartProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.WalmartProduct
        fields = '__all__'


class AmazonProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.AmazonProduct
        fields = '__all__'


class NutritionFactsSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.NutritionFacts
        fields = '__all__'


class ProductSerializer(serializers.HyperlinkedModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['loblaws_product', ]
    # _SELECT_RELATED_FIELDS = ['nutrition_facts', ]

    id = serializers.ReadOnlyField()

    loblaws_product = LoblawsProductSerializer()

    # nutrition_facts = NutritionFactsSerializer()

    walmart_product = WalmartProductSerializer()

    # amazon_product = AmazonProductSerializer()

    class Meta:
        model = models.Product
        reverse_relationships = [
            'loblaws_product',
            'walmart_product',
            # 'amazon_product',
            # 'nutrition_facts'
        ]
        fields = ['id', 'url', 'created', 'modified', 'product_code', 'description', 'breadcrumbs_array', 'name',
                  'brand', 'store', 'price', 'upc_code',
                  'nutrition_available'] + reverse_relationships


class ProductImageSerializer(serializers.HyperlinkedModelSerializer):
    product = ProductSerializer()

    class Meta:
        model = models.ProductImage
        fields = '__all__'


class FrontOfPackLabelSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    product_image = ProductImageSerializer()

    class Meta:
        model = models.FrontOfPackLabel
        fields = '__all__'


class AdvancedProductSerializer(serializers.ModelSerializer, EagerLoadingMixin):
    """
    Serializer for the Advanced Search app. Provides detailed product info + nutrition facts.
    """
    _SELECT_RELATED_FIELDS = ['loblaws_product', 'nutrition_facts']

    id = serializers.ReadOnlyField()

    loblaws_product = LoblawsProductSerializer()
    nutrition_facts = NutritionFactsSerializer()

    class Meta:
        model = models.Product
        reverse_relationships = [
            'loblaws_product',
            # 'walmart_product',
            # 'amazon_product',
            'nutrition_facts'
        ]
        fields = ['id', 'url', 'product_code', 'name', 'brand', 'store', 'price',
                  'upc_code'] + reverse_relationships


class ProductNameSerializer(serializers.ModelSerializer):
    """ Simple serializer for storing only product names """
    id = serializers.ReadOnlyField()
    text = serializers.CharField(source='name')

    class Meta:
        model = models.Product
        fields = ['id', 'text']


class BrandNameSerializer(serializers.ModelSerializer):
    """ Simple serializer for storing only product names """
    id = serializers.ReadOnlyField()
    text = serializers.CharField(source='brand')

    class Meta:
        model = models.Product
        fields = ['id', 'text']


class LoblawsBreadcrumbSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.LoblawsProduct
        fields = (
            'id', 'product', 'breadcrumbs_array'
        )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
