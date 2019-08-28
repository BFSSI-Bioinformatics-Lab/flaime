from django.contrib.auth.models import Group
from flaim.database import models
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class LoblawsProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.LoblawsProduct
        # fields = '__all__'
        fields = ('id', 'section', 'subcategory', 'url', 'description', 'image_directory')


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


class ProductSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()
    loblaws_product = LoblawsProductSerializer()
    walmart_product = WalmartProductSerializer()
    amazon_product = AmazonProductSerializer()
    nutrition_facts = NutritionFactsSerializer()

    class Meta:
        model = models.Product
        reverse_relationships = ['loblaws_product', 'walmart_product', 'amazon_product', 'nutrition_facts']
        fields = ['id', 'url', 'created', 'modified', 'product_code', 'name', 'brand', 'store', 'price', 'upc_code',
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


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
