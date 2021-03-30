from django.forms import ModelForm
from flaim.database.models import Product

class ProductUpdateForm(ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'brand')
