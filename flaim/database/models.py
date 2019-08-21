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
    product_code = models.CharField(max_length=100)
    name = models.CharField(max_length=300, unique=False, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)

    VALID_STORES = (
        ('LOBLAWS', 'Loblaws'),
        ('WALMART', 'Walmart'),
        ('AMAZON', 'Amazon')
    )
    store = models.CharField(max_length=7, choices=VALID_STORES)
    price = models.CharField(max_length=15, blank=True, null=True)
    upc_code = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)  # e.g. from Amazon technical details
    nutrition_available = models.BooleanField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    scrape_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_code}: {self.name}"

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'


class NutritionFacts(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="nutrition_facts")
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

    def extract_number_from_nutrient(self, val: str) -> Union[tuple, None]:
        """
        Given an input nutrient string, will return the float value while handling unit conversion if necessary
        """
        # Grab the units from the nutrient string
        nutrient_type = self.detect_units(val)
        if nutrient_type is None:
            return

        # Grab the numeric float value from the string
        nutrient_float = float(val.split(nutrient_type)[0].strip())

        # Grams & Milligrams (normalizes everything into grams)
        if nutrient_type == 'g':
            return nutrient_float, 'g'
        elif nutrient_type == 'mg' or nutrient_type == "milligrams":
            return self.convert_milligrams_to_grams(nutrient_float), 'g'

        # Percent DV (values on nutrition labels are integers ranging from 0% -> n%, so we convert to float)
        if nutrient_type == "dv" or nutrient_type == "%":
            return float(nutrient_float / 100), '%'

        # Calories
        if nutrient_type == "cal" or nutrient_type == "Cal" or nutrient_type == "calories":
            return int(nutrient_float), 'cal'

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
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="loblaws_product")
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
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="walmart_product")

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Walmart Product'
        verbose_name_plural = 'Walmart Products'


# AMAZON MODELS

class AmazonProduct(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="amazon_product")
    bullet_points = models.TextField(null=True, blank=True)  # The Amazon description field
    manufacturer_reference = models.CharField(max_length=100, blank=True,
                                              null=True)  # e.g. from Amazon technical details
    speciality = models.CharField(max_length=100, blank=True, null=True)  # e.g. Kosher
    units = models.CharField(max_length=30, blank=True, null=True)  # e.g. 2.5 Kilograms
    item_weight = models.CharField(max_length=30, blank=True, null=True)  # e.g. 1.58 kg
    parcel_dimensions = models.CharField(max_length=30, blank=True, null=True)  # e.g. 30 x 30 x 30 cm
    date_first_available = models.DateField(null=True, blank=True)  # from the Additional Information table

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Amazon Product'
        verbose_name_plural = 'Amazon Products'


class AmazonSearchResult(TimeStampedModel):
    """ Stores information on the search page that a particular product showed up on """
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_search_result")
    search_string = models.CharField(max_length=200)  # Search string used to generate results
    page = models.IntegerField()  # Page that the product showed up on
    item_number = models.IntegerField()  # Of products shown on search page, tracks the index of the product (i.e. 2nd)


class AmazonProductReview(TimeStampedModel):
    # One Amazon Product will have many reviews
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_product_reviews")
    review_title = models.CharField(max_length=300)
    review_text = models.TextField(blank=True, null=True)
    reviewer_username = models.CharField(max_length=100)
    rating = models.FloatField()  # e.g. 3 out of 5 stars -> convert to float
    helpful = models.BooleanField()  # Flag for if the review was marked as helpful or not by Amazon


# IMAGE CLASSIFICATION

class ProductImageClassification(TimeStampedModel):
    """ Stores basic classification information on a product image """
    # Required fields
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="image_classification")
    image_path = models.CharField(max_length=1000)
    image_number = models.IntegerField()  # Order of the image in a set for a product

    # Classification can be populated after the fact as it can take time to calculate
    classification_choices = (
        ('NUTRITION', 'N'),
        ('INGREDIENTS', 'I'),
        ('OTHER', 'O'),
    )
    classification = models.CharField(choices=classification_choices, max_length=15, null=True, blank=True)

    class Meta:
        verbose_name = 'Image Classification'
        verbose_name_plural = 'Image Classifications'
