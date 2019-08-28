from django.test import TestCase
from flaim.database import models

"""
https://realpython.com/test-driven-development-of-a-django-restful-api/
"""


class ProductTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        print("setUpTestData: Run once to set up non-modified data for all class methods.")
        models.Product.objects.create(
            product_code="EA_000000",
            name="Test Product Name",
            brand="Kelloggs",
            store="WALMART",
        )

    def setUp(self):
        print("setUp: Run once for every test method to setup clean data.")
        pass

    def test_store(self):
        obj = models.Product.objects.get(product_code="EA_000000")
        self.assertEqual(obj.store, "WALMART")


class NutritionFactsTest(TestCase):
    pass
