import logging

from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework import serializers, views
from flaim.database import models

User = get_user_model()

logger = logging.getLogger(__name__)


class NutritionFactsSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = models.NutritionFacts
        fields = '__all__'


class Test(viewsets.ModelViewSet):
    queryset = models.NutritionFacts.objects.all()
    serializer_class = NutritionFactsSerializer

    def get(self, request):
        """
        Return a list of all users.
        """
        logger.info('hi')
        print('hi')

        return Response({
            "test": "arbitrary",
        })
