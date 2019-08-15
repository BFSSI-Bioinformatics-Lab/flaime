from django.shortcuts import render
from django.contrib.auth.models import Group
from rest_framework import viewsets

from flaim.database import models
from flaim.database import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your views here.
class ProductViewSet(viewsets.ModelViewSet):
    queryset = models.Product.objects.all().order_by('-created')
    serializer_class = serializers.ProductSerializer


class NutritionFactsViewSet(viewsets.ModelViewSet):
    queryset = models.NutritionFacts.objects.all().order_by('-created')
    serializer_class = serializers.NutritionFactsSerializer


class LoblawsProductViewSet(viewsets.ModelViewSet):
    queryset = models.LoblawsProduct.objects.all().order_by('-created')
    serializer_class = serializers.LoblawsProductSerializer


class WalmartProductViewSet(viewsets.ModelViewSet):
    queryset = models.WalmartProduct.objects.all().order_by('-created')
    serializer_class = serializers.WalmartProductSerializer


class AmazonProductViewSet(viewsets.ModelViewSet):
    queryset = models.AmazonProduct.objects.all().order_by('-created')
    serializer_class = serializers.AmazonProductSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('-name')
    serializer_class = serializers.GroupSerializer
