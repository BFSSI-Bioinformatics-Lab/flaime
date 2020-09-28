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


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


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
        fields = (
            'url', 'id', 'image_directory', 'sku', 'bullets', 'dietary_info',
        )


class AmazonProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.AmazonProduct
        fields = '__all__'


class NutritionFactsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.NutritionFacts
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    calculated_best_category = serializers.SerializerMethodField()
    verified_by = UserSerializer()

    class Meta:
        model = models.Category
        fields = (
            'id',
            'predicted_category_1', 'confidence_1', 'predicted_category_2', 'confidence_2', 'predicted_category_3',
            'confidence_3', 'manual_category', 'verified', 'verified_by', 'model_version', 'calculated_best_category'
        )

    @staticmethod
    def get_calculated_best_category(obj):
        if obj.manual_category is None:
            return obj.predicted_category_1
        return obj.manual_category


class SubcategorySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    verified_by = UserSerializer()
    calculated_best_subcategory = serializers.SerializerMethodField()
    parent_category = CategorySerializer()

    class Meta:
        model = models.Subcategory
        fields = (
            'id',
            'predicted_subcategory_1', 'confidence_1', 'predicted_subcategory_2', 'confidence_2',
            'predicted_subcategory_3',
            'confidence_3', 'manual_subcategory', 'verified', 'verified_by', 'model_version',
            'parent_category', 'calculated_best_subcategory'
        )

    @staticmethod
    def get_calculated_best_subcategory(obj):
        if obj.manual_subcategory is None:
            return obj.predicted_subcategory_1
        return obj.manual_subcategory


class RecentProductSerializer(serializers.HyperlinkedModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['loblaws_product', 'walmart_product']

    id = serializers.ReadOnlyField()
    loblaws_product = LoblawsProductSerializer()
    walmart_product = WalmartProductSerializer()
    category = CategorySerializer()
    batch = ScrapeBatchSerializer()
    scrape_date = serializers.ReadOnlyField(source='batch.scrape_date')

    class Meta:
        model = models.Product
        reverse_relationships = [
            'loblaws_product',
            'walmart_product'
        ]
        fields = ['id', 'url', 'created', 'modified', 'product_code', 'description', 'breadcrumbs_array', 'name',
                  'brand', 'store', 'price', 'upc_code', 'nutrition_available', 'scrape_date',
                  'batch', 'category'] + reverse_relationships


class ProductSerializer(serializers.HyperlinkedModelSerializer, EagerLoadingMixin):
    _SELECT_RELATED_FIELDS = ['loblaws_product', 'walmart_product']

    # Add category field

    id = serializers.ReadOnlyField()
    loblaws_product = LoblawsProductSerializer()
    walmart_product = WalmartProductSerializer()
    category = CategorySerializer()
    subcategory = SubcategorySerializer()
    batch = ScrapeBatchSerializer()
    scrape_date = serializers.ReadOnlyField(source='batch.scrape_date')
    url = serializers.HyperlinkedIdentityField(view_name='products-detail', lookup_field='pk')

    class Meta:
        model = models.Product
        reverse_relationships = [
            'loblaws_product',
            'walmart_product',
            'batch',
            'category',
            'subcategory'
        ]
        fields = ['id', 'url', 'created', 'modified', 'product_code', 'description', 'breadcrumbs_array', 'name',
                  'brand', 'store', 'price', 'upc_code',
                  'nutrition_available', 'scrape_date'] + reverse_relationships


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
    _SELECT_RELATED_FIELDS = ['loblaws_product', 'walmart_product', 'nutrition_facts']

    id = serializers.ReadOnlyField()
    loblaws_product = LoblawsProductSerializer()
    walmart_product = WalmartProductSerializer()
    nutrition_facts = NutritionFactsSerializer()
    category = CategorySerializer()
    subcategory = SubcategorySerializer()
    images = serializers.SlugRelatedField(many=True, read_only=True, slug_field='image_string')
    url = serializers.HyperlinkedIdentityField(view_name='advanced_products-detail', lookup_field='pk')

    def update(self, instance, validated_data):
        """
        This override method of update allows for the Product Curator page to update the 'manual_category' and
        'verified' fields. For some reason, I can't get datatables to correctly PATCH data to DRF; the validated_data
        dict comes in empty. This is not an issue when I execute a PATCH directly via Postman, so the datatables ajax
        config on producted_curator/index.html is probably not done correctly.

        The workaround is to pull the data from self.initial_data (this is where the datatables ajax patch data is
        stored) and force it into validated_data.
        """

        # Check if the validated_data dict is empty/doesn't contain expected results
        if 'category' not in validated_data:
            validated_data = self.initial_data['data'][str(self.data['id'])]

        predicted_category_data = validated_data.pop('category')
        category = instance.category
        user = User.objects.get(username=predicted_category_data.get('user', category.verified_by))
        category.manual_category = predicted_category_data.get('manual_category', category.manual_category)
        category.verified = predicted_category_data.get('verified', category.verified)
        category.verified_by = user
        category.save()

        # Store the generic relationship between product code and category
        product_mapping, created = models.CategoryProductCodeMappingSupport.objects.get_or_create(
            product_code=instance.product_code)
        product_mapping.category = category.manual_category
        product_mapping.verified_by = user
        product_mapping.save()

        return instance

    class Meta:
        model = models.Product
        lookup_field = 'pk'
        reverse_relationships = [
            'loblaws_product',
            'walmart_product',
            'nutrition_facts',
            'category',
            'subcategory'
        ]
        fields = ['id', 'url', 'product_code', 'name', 'brand', 'store', 'price',
                  'upc_code', 'images'] + reverse_relationships


class ProductNameSerializer(serializers.ModelSerializer):
    """ Simple serializer for storing only product names """
    id = serializers.ReadOnlyField()
    text = serializers.CharField(source='name')

    class Meta:
        model = models.Product
        fields = ['id', 'text']


class BrandNameSerializer(serializers.ModelSerializer):
    """ Simple serializer for storing only brand names """
    id = serializers.ReadOnlyField()
    text = serializers.CharField(source='brand')

    class Meta:
        model = models.Product
        fields = ['id', 'text']


class CategoryNameSerializer(serializers.ModelSerializer):
    """
    Simple serializer for storing only predicted category names.
    Fields are named for compatibiltiy with select2
    """
    id = serializers.ReadOnlyField()
    text = serializers.CharField(source='predicted_category_1')

    class Meta:
        model = models.Category
        fields = ['id', 'text']


class LoblawsBreadcrumbSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.LoblawsProduct
        fields = (
            'id', 'product', 'breadcrumbs_array'
        )
