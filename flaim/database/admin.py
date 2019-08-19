from django.contrib import admin
from flaim.database import models

# Register your models here.
admin.site.register(models.Product)
admin.site.register(models.LoblawsProduct)
admin.site.register(models.AmazonProduct)
admin.site.register(models.WalmartProduct)
admin.site.register(models.NutritionFacts)
