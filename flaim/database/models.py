from django.db import models
from typing import Optional, Union

from flaim.database.nutrient_coding import VALID_NUTRIENT_COLUMNS


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-
    updating ``created`` and ``modified`` fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# GENERAL MODELS

class Product(TimeStampedModel):
    name = models.CharField(max_length=300, unique=False)
    brand = models.CharField(max_length=100)

    VALID_STORES = (
        ('LOBLAWS', 'Loblaws'),
        ('WALMART', 'Walmart'),
        ('AMAZON', 'Amazon')
    )
    store = models.CharField(max_length=7, choices=VALID_STORES)
    product_code = models.CharField(max_length=100)
    upc_code = models.CharField(max_length=100, blank=True, null=True)
    nutrition_available = models.BooleanField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    scrape_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_code}: {self.name}"

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class NutritionFacts(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)
    total_size = models.CharField(max_length=100, blank=True, null=True)
    serving_size_raw = models.CharField(max_length=100, blank=True, null=True)
    serving_size = models.IntegerField(blank=True, null=True)

    SERVING_SIZE_UNITS = (
        ('g', 'grams'),
        ('mL', 'millilitres')
    )
    serving_size_units = models.CharField(max_length=11, choices=SERVING_SIZE_UNITS, blank=True, null=True)
    ingredients = models.TextField(blank=True, null=True)

    # Nutrients
    calories = models.IntegerField(blank=True, null=True)
    sodium = models.FloatField(blank=True, null=True)
    sodium_dv = models.FloatField(blank=True, null=True)
    calcium = models.FloatField(blank=True, null=True)
    calcium_dv = models.FloatField(blank=True, null=True)
    total_fat = models.FloatField(blank=True, null=True)
    total_fat_dv = models.FloatField(blank=True, null=True)
    monounsaturated_fat = models.FloatField(blank=True, null=True)
    polyunsaturated_fat = models.FloatField(blank=True, null=True)
    saturated_fat = models.FloatField(blank=True, null=True)
    saturated_fat_dv = models.FloatField(blank=True, null=True)
    trans_fat = models.FloatField(blank=True, null=True)
    trans_fat_dv = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    potassium_dv = models.FloatField(blank=True, null=True)
    total_carbohydrate = models.FloatField(blank=True, null=True)
    total_carbohydrate_dv = models.FloatField(blank=True, null=True)
    dietary_fibre = models.FloatField(blank=True, null=True)
    dietary_fibre_dv = models.FloatField(blank=True, null=True)
    sugars = models.FloatField(blank=True, null=True)
    sugars_dv = models.FloatField(blank=True, null=True)
    protein = models.FloatField(blank=True, null=True)
    cholesterol = models.FloatField(blank=True, null=True)
    vitamin_a = models.FloatField(blank=True, null=True)
    vitamin_a_dv = models.FloatField(blank=True, null=True)
    vitamin_c = models.FloatField(blank=True, null=True)
    vitamin_c_dv = models.FloatField(blank=True, null=True)
    vitamin_d = models.FloatField(blank=True, null=True)
    vitamin_e = models.FloatField(blank=True, null=True)
    niacin = models.FloatField(blank=True, null=True)
    vitamin_b6 = models.FloatField(blank=True, null=True)
    folacin = models.FloatField(blank=True, null=True)
    folate = models.FloatField(blank=True, null=True)
    vitamin_b12 = models.FloatField(blank=True, null=True)
    pantothenic_acid = models.FloatField(blank=True, null=True)
    pantothenate = models.FloatField(blank=True, null=True)
    alcohol = models.FloatField(blank=True, null=True)
    carbohydrate = models.FloatField(blank=True, null=True)
    erythritol = models.FloatField(blank=True, null=True)
    glycerol = models.FloatField(blank=True, null=True)
    isomalt = models.FloatField(blank=True, null=True)
    lactitol = models.FloatField(blank=True, null=True)
    maltitol = models.FloatField(blank=True, null=True)
    mannitol = models.FloatField(blank=True, null=True)
    polydextrose = models.FloatField(blank=True, null=True)
    sorbitol = models.FloatField(blank=True, null=True)
    xylitol = models.FloatField(blank=True, null=True)
    iron = models.FloatField(blank=True, null=True)
    iron_dv = models.FloatField(blank=True, null=True)
    riboflavin = models.FloatField(blank=True, null=True)
    selenium = models.FloatField(blank=True, null=True)
    magnesium = models.FloatField(blank=True, null=True)
    phosphorus = models.FloatField(blank=True, null=True)
    thiamine = models.FloatField(blank=True, null=True)
    zinc = models.FloatField(blank=True, null=True)

    nutrition_raw_text = models.TextField(blank=True, null=True)

    @staticmethod
    def detect_units(val: str) -> Optional[str]:
        """
        Method to detect units in a nutrient value string.
        :param val: string for nutrient value e.g. 30 g, 50 cal, 500 mg,  etc.
        :return: string containing units for input value
        """
        # Milligrams
        if 'mg' in val:
            return 'mg'
        elif 'milligrams' in val:
            return 'milligrams'
        # Calories
        elif 'calories' in val:
            return 'calories'
        elif 'Cal' in val:
            return 'Cal'
        elif 'cal' in val:
            return 'cal'
        # % DV
        elif '%' in val:
            return '%'
        elif 'dv' in val:
            return 'dv'
        # Grams
        elif 'g' in val or 'grams' in val:
            return 'g'
        else:
            print(f"WARNING: Could not detect any units in value ({val})")
            return None

    def extract_number_from_nutrient(self, val: str) -> Union[int, float, None]:
        """
        Given an input nutrient string, will return the float value while handling unit conversion if necessary
        """
        nutrient_type = self.detect_units(val)
        if nutrient_type is None:
            return
        nutrient_float = float(val.split(nutrient_type)[0].strip())

        # Grams & Milligrams
        if nutrient_type == 'g':
            return nutrient_float
        elif nutrient_type == 'mg' or nutrient_type == "milligrams":
            return self.convert_milligrams_to_grams(nutrient_float)

        # Percent DV (values on nutrition labels are integers ranging from 0% -> n%, so we convert to float)
        if nutrient_type == "dv" or nutrient_type == "%":
            return float(nutrient_float / 100)

        # Calories
        if nutrient_type == "cal" or nutrient_type == "Cal" or nutrient_type == "calories":
            return int(nutrient_float)

    @staticmethod
    def convert_milligrams_to_grams(val: float) -> float:
        return val * 0.001

    @staticmethod
    def valid_nutrient(nutrient: str) -> bool:
        # Grab list of attributes
        if nutrient in VALID_NUTRIENT_COLUMNS:
            print(f"Detected '{nutrient}'")
            return True
        else:
            print(f"Value '{nutrient}' is not a valid database column")
            return False

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Product Nutrition'
        verbose_name_plural = 'Product Nutrition'


# LOBLAWS MODELS

class LoblawsProduct(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image_directory = models.CharField(max_length=500, blank=True, null=True)
    breadcrumbs = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Loblaws Product'
        verbose_name_plural = 'Loblaws Products'


# WALMART MODELS

class WalmartProduct(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Walmart Product'
        verbose_name_plural = 'Walmart Products'


# AMAZON MODELS

class AmazonProduct(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Amazon Product'
        verbose_name_plural = 'Amazon Products'
