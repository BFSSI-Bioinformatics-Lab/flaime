from django.contrib import admin
from flaim.database import models


# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    raw_id_fields = ('batch', 'category')


admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.ScrapeBatch)
admin.site.register(models.NutritionFacts)
admin.site.register(models.ProductImage)

admin.site.register(models.LoblawsProduct)

admin.site.register(models.WalmartProduct)

admin.site.register(models.AmazonProduct)
admin.site.register(models.AmazonProductReview)
admin.site.register(models.AmazonSearchResult)

admin.site.register(models.FrontOfPackLabel)
admin.site.register(models.NutritionLabelClassification)

admin.site.register(models.Category)
admin.site.register(models.CategoryProductCodeMappingSupport)
admin.site.register(models.ReferenceCategorySupport)
