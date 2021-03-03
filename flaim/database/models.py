from time import strftime
from pathlib import Path
from django.db import models
from typing import Optional, Union
from django.contrib.postgres.fields import JSONField, ArrayField
from flaim.database.product_mappings import VALID_NUTRIENT_COLUMNS, \
    REFERENCE_SUBCATEGORIES_CODING_DICT, REFERENCE_CATEGORIES_CODING_DICT
from simple_history.models import HistoricalRecords
from flaim.users.models import User

# Sensible field sizes for CharField columns
LG_CHAR = 1500
MD_CHAR = 500
SM_CHAR = 50
VALID_STORES = (
    ('LOBLAWS', 'Loblaws'),
    ('WALMART', 'Walmart'),
    ('VOILA', 'Voila'),
    ('GROCERYGATEWAY', 'Grocery Gateway'),
    ('AMAZON', 'Amazon')
)


def upload_product_image(obj):
    """ Sets the directory for an input ProductImage """
    store = obj.product.store
    date = strftime("%Y%m%d")
    return f"{store}/{date}"


def upload_fop_image(obj):
    """
    Note: obj must be instance of ProductImage model

    Takes the parent product_image name e.g. /LOBLAWS/20190101/something.jpg and morphs it into
    /LOBLAWS/20190101/something_fop.jpg

    Reference for how ImageField attributes can be accessed:
    https://docs.djangoproject.com/en/2.2/topics/files/
    """
    parent_path = Path(obj.product_image.image_path.name)  # e.g. /LOBLAWS/20190101/something.jpg
    suffix = parent_path.suffix
    fop_path = parent_path.with_suffix(f'_FOP{suffix}')
    return fop_path


def safe_run(func):
    """ Decorator to run a method wrapped in a try/except -> returns None upon exception """

    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return None

    return func_wrapper


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
class ScrapeBatch(models.Model):
    """
    Upon submission of a scraping job, that job is assigned an ID using this table and any products collected throughout
    the job will be nested beneath it.
    """
    scrape_date = models.DateField(null=True)  # Should be populated manually once scrape job is complete

    # Scraper specifics
    store = models.CharField(max_length=SM_CHAR, choices=VALID_STORES)

    # Version of web scraper
    scraper_version = models.CharField(max_length=SM_CHAR, blank=True, null=True)

    # Total number of products retrieved from the scrape
    total_products = models.IntegerField(blank=True, null=True)

    # Number of products that aren't yet in the database yet
    new_products = models.IntegerField(blank=True, null=True)

    # Number of products that are in the database but not in the scrape batch
    missing_products = models.IntegerField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.scrape_date}"

    class Meta:
        verbose_name = 'Scrape Batch'
        verbose_name_plural = 'Scrape Batches'


class ReferenceCategorySupport(models.Model):
    """
    Support table to store short and long forms of reference categories according to
    https://www.canada.ca/en/health-canada/services/technical-documents-labelling-requirements/table-reference-amounts-food.html
    """
    category_id = models.CharField(max_length=SM_CHAR)
    category_name = models.CharField(max_length=MD_CHAR)
    subcategory_id = models.CharField(max_length=SM_CHAR)
    subcategory_name = models.CharField(max_length=MD_CHAR)
    reference_amount_raw = models.CharField(max_length=SM_CHAR)  # Raw unparsed value, stored for reference

    def __str__(self):
        return f'{self.category_id} {self.category_name} - {self.subcategory_id} {self.subcategory_name}'

    class Meta:
        verbose_name = 'Reference Category'
        verbose_name_plural = 'Reference Categories'

    @staticmethod
    def parse_reference_amount(reference_amount_raw: str) -> [float, str, str]:
        """
        parses reference_amount_raw into reference_amount, reference_amount_units and reference_amount_extra
        The code here is stupid but the source data should not change so the brittle logic is good enough.
        Original raw data: flaim/docs/reference_amounts_2016.csv
        """
        values = reference_amount_raw.split(" ", 2)
        reference_amount = values[0].strip()
        reference_amount_units = values[1].strip()  # g or mL

        # Grab the extra value if available (e.g. "cooked", "raw")
        if len(values) > 2:
            reference_amount_extra = values[3]
        else:
            reference_amount_extra = None

        # Abort if it's one of the weird values (e.g. "Amount to make 250 mL of drink")
        if reference_amount_units not in ['g', 'mL']:
            reference_amount, reference_amount_units, reference_amount_extra = None, None, None

        return reference_amount, reference_amount_units, reference_amount_extra


class Category(TimeStampedModel):
    """
    predicted_category_1, 2 and 3 correspond to the top 3 predictions

    "manual category" is set when a user corrects a category via the ProductCurator app
    "verified" represents whether or not the prediction has been manually verified/confirmed by a user
    "verified_by" represents User who verified the category
    """
    predicted_category_1 = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    confidence_1 = models.FloatField(blank=True, null=True)

    predicted_category_2 = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    confidence_2 = models.FloatField(blank=True, null=True)

    predicted_category_3 = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    confidence_3 = models.FloatField(blank=True, null=True)

    # This field allows for a user to manually select a category/confirm the predicted category
    manual_category = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    model_version = models.CharField(max_length=SM_CHAR, blank=True, null=True)

    def get_related_subcategories(self) -> [str]:
        """ Returns a list of related subcategories for the best category available for this record """
        subcategories = [x.subcategory for x in
                         ReferenceCategorySupport.objects.filter(category__icontains=self.best_category)]
        return subcategories

    @property
    def best_category(self) -> str:
        if self.manual_category is None:
            return self.predicted_category_1
        return self.manual_category

    def __str__(self):
        """
        Return manual category if available, otherwise return the best guess.
        """
        if self.manual_category is None:
            return f'{self.predicted_category_1} ({self.confidence_1:.2f})'
        return self.manual_category

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class Subcategory(TimeStampedModel):
    """
    Similar to the Category model, intended to capture subcategory values for products.
    """
    parent_category = models.ForeignKey(ReferenceCategorySupport, on_delete=models.CASCADE, blank=True, null=True)

    predicted_subcategory_1 = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    confidence_1 = models.FloatField(blank=True, null=True)

    # This field allows for a user to manually select a category/confirm the predicted category
    manual_subcategory = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    model_version = models.CharField(max_length=SM_CHAR, blank=True, null=True)

    @property
    def best_subcategory(self):
        if self.manual_subcategory is None:
            return self.predicted_subcategory_1
        return self.manual_subcategory

    def __str__(self):
        """
        Return manual subcategory if available, otherwise return the best guess.
        """
        if self.manual_subcategory is None:
            return f'{self.predicted_subcategory_1} ({self.confidence_1:.2f})'
        return self.manual_subcategory

    class Meta:
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'


class Product(TimeStampedModel):
    product_code = models.CharField(max_length=MD_CHAR)
    name = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    brand = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Flag to indicate if this is the most recently uploaded version of a product
    most_recent = models.BooleanField(default=True)

    # Flag to indicate whether the product is a variety pack or not
    variety_pack = models.BooleanField(default=False)

    # TODO: Accomodate the possibility for multiple breadcrumb trails, i.e. change to ArrayField(ArrayField)
    breadcrumbs_text = models.CharField(max_length=LG_CHAR, blank=True, null=True)
    breadcrumbs_array = ArrayField(models.CharField(max_length=MD_CHAR), blank=True, null=True)

    # TODO: Make batch field required upon instantiation once we move towards a more production-ready version of FLAIME
    batch = models.ForeignKey(ScrapeBatch, on_delete=models.CASCADE, blank=True, null=True)

    store = models.CharField(max_length=SM_CHAR, choices=VALID_STORES)
    price = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    price_float = models.FloatField(blank=True, null=True)
    price_units = models.CharField(max_length=SM_CHAR, blank=True, null=True)
    upc_code = models.CharField(max_length=MD_CHAR, blank=True, null=True)
    upc_array = ArrayField(models.CharField(max_length=MD_CHAR), blank=True, null=True)
    nutrition_available = models.BooleanField(blank=True, null=True)
    unidentified_nft_format = models.BooleanField(default=False)  # Bool flag for whether the NFT is American or not
    nielsen_product = models.BooleanField(blank=True, null=True)
    url = models.CharField(max_length=LG_CHAR, blank=True, null=True)
    atwater_result = models.CharField(max_length=SM_CHAR, blank=True, null=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.SET_NULL, blank=True, null=True)

    history = HistoricalRecords(related_name='product_history')

    @staticmethod
    def generate_existing_product_codes_dict(store: str) -> dict:
        """
        Method to generate id:product_code dict. Ideally use this method once to retrieve the dict and then refer to it
        for detecting which products to update for the most_recent field.

        :param store: filters product list based on store string e.g. 'LOBLAWS', 'WALMART'
        :return: id:product_code dictionary
        """
        existing_codes = Product.objects.filter(store=store).values_list('id', 'product_code')
        existing_codes_dict = dict(existing_codes)
        return existing_codes_dict

    @staticmethod
    def test_if_most_recent(product_code: str, existing_codes_dict: dict) -> [int]:
        """
        Given a name and brand retrieved from a recent scrape, as well as the existing_product_codes_dict from
        generate_existing_product_codes_dict(), will figure out which IDs (if any) need to have their most_recent
        flag set to False

        :param product_code: Product code from scrape
        :param existing_codes_dict: Dictionary generated with generate_existing_product_codes_dict()
        :return:
        """
        # List to store ids of products to change value of most_recent to False
        ids_to_demote = []
        for key, val in existing_codes_dict.items():
            # Duplicate product detected
            if val == product_code:
                ids_to_demote.append(key)
        return ids_to_demote

    @staticmethod
    def demote_most_recent_product_list(id_list: [int]):
        """
        Takes in a list of IDs, retrieves each object in DB, and sets their most_recent flag to False
        :param id_list: list of integer IDs
        """
        if len(id_list) > 0:
            products = Product.objects.filter(id__in=id_list)
            for p in products:
                p.most_recent = False
                p.save()

    @property
    def images(self):
        """ Returns all images associated with the product"""
        return ProductImage.objects.filter(product__product_code=self.product_code)

    def __str__(self):
        return f"{self.product_code}: {self.name}"

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        indexes = [
            models.Index(fields=[
                'product_code',
                'most_recent'
            ])
        ]


class VarietyPackProductCodeMappingSupport(models.Model):
    """
    Support table to permanently store relationship between a retailer product code and whether or not the product
    is a variety pack (e.g. containing mulitple individual products)

    Records can be created manually either through the manage.py shell command or through the admin interface.
    Any newly uploaded products will automatically be assigned a variety pack status if a record is found in this table.

    TODO: Implement web interface to allow users flag these
    """
    product_code = models.CharField(max_length=MD_CHAR, unique=True)
    variety_pack = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.product_code}: {self.variety_pack}'

    class Meta:
        verbose_name = 'Variety Pack:Product Code Mapping'
        verbose_name_plural = 'Variety Pack:Product Code Mappings'


class CategoryProductCodeMappingSupport(models.Model):
    """
    Support table intended to permanently store a mapping between categories and store-specific product codes
    Can be expanded to contain other arbitrary product_code:category mappings

    When a user manually corrects a predicted category for a particular product, this table should be automatically
    updated.

    When a new scrape batch is uploaded, each product should be automatically assigned a category if a value has been
    added to this table.
    """
    product_code = models.CharField(max_length=MD_CHAR, unique=True)
    PRODUCT_CATEGORIES_TUPLES = [(x, x) for x in REFERENCE_CATEGORIES_CODING_DICT.values()]
    PRODUCT_SUBCATEGORY_TUPLES = [(x, x) for x in REFERENCE_SUBCATEGORIES_CODING_DICT.values()]
    category = models.CharField(max_length=MD_CHAR, choices=PRODUCT_CATEGORIES_TUPLES)
    subcategory = models.CharField(max_length=MD_CHAR, choices=PRODUCT_SUBCATEGORY_TUPLES, blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.product_code}: {self.category} - {self.subcategory}'

    class Meta:
        verbose_name = 'Category:Product Code Mapping'
        verbose_name_plural = 'Category:Product Code Mappings'


class ProductLink(TimeStampedModel):
    # TODO: Table to store relationships between linked products, e.g. 100g corn pops vs. 1kg corn pops
    pass


class NutritionFacts(TimeStampedModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="nutrition_facts")
    total_size = models.CharField(max_length=MD_CHAR, blank=True,
                                  null=True)  # Should be serving_size * # of servings in product
    serving_size_raw = models.CharField(max_length=MD_CHAR, blank=True, null=True)  # Unparsed serving size text
    serving_size = models.IntegerField(blank=True, null=True)  # Parsed numeric serving size value

    SERVING_SIZE_UNITS = (
        ('g', 'grams'),
        ('mL', 'millilitres')
    )
    serving_size_units = models.CharField(max_length=SM_CHAR, choices=SERVING_SIZE_UNITS, blank=True, null=True)

    ingredients = models.TextField(blank=True, null=True)

    # Nutrients - units should always be represented as grams
    calories = models.IntegerField(blank=True, null=True)
    sodium = models.FloatField(blank=True, null=True)
    sodium_dv = models.FloatField(blank=True, null=True)
    calcium = models.FloatField(blank=True, null=True)
    calcium_dv = models.FloatField(blank=True, null=True)
    totalfat = models.FloatField(blank=True, null=True)
    totalfat_dv = models.FloatField(blank=True, null=True)
    monounsaturated_fat = models.FloatField(blank=True, null=True)
    polyunsaturated_fat = models.FloatField(blank=True, null=True)
    omega3fattyacids = models.FloatField(blank=True, null=True)
    saturatedfat = models.FloatField(blank=True, null=True)
    saturatedfat_dv = models.FloatField(blank=True, null=True)
    transfat = models.FloatField(blank=True, null=True)
    transfat_dv = models.FloatField(blank=True, null=True)
    potassium = models.FloatField(blank=True, null=True)
    potassium_dv = models.FloatField(blank=True, null=True)
    totalcarbohydrate = models.FloatField(blank=True, null=True)
    totalcarbohydrate_dv = models.FloatField(blank=True, null=True)
    othercarbohydrates = models.FloatField(blank=True, null=True)
    dietaryfiber = models.FloatField(blank=True, null=True)
    dietaryfiber_dv = models.FloatField(blank=True, null=True)
    sugar = models.FloatField(blank=True, null=True)
    protein = models.FloatField(blank=True, null=True)
    cholesterol = models.FloatField(blank=True, null=True)
    cholesterol_dv = models.FloatField(blank=True, null=True)
    vitamina = models.FloatField(blank=True, null=True)
    vitamina_dv = models.FloatField(blank=True, null=True)
    vitaminc = models.FloatField(blank=True, null=True)
    vitaminc_dv = models.FloatField(blank=True, null=True)
    vitamind = models.FloatField(blank=True, null=True)
    vitamine = models.FloatField(blank=True, null=True)
    niacin = models.FloatField(blank=True, null=True)
    vitaminb6 = models.FloatField(blank=True, null=True)
    folacin = models.FloatField(blank=True, null=True)
    folate = models.FloatField(blank=True, null=True)
    vitaminb12 = models.FloatField(blank=True, null=True)
    pantothenicacid = models.FloatField(blank=True, null=True)
    pantothenate = models.FloatField(blank=True, null=True)
    alcohol = models.FloatField(blank=True, null=True)
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
    magnesium_dv = models.FloatField(blank=True, null=True)
    phosphorus = models.FloatField(blank=True, null=True)
    phosphorus_dv = models.FloatField(blank=True, null=True)
    thiamine = models.FloatField(blank=True, null=True)
    zinc = models.FloatField(blank=True, null=True)
    history = HistoricalRecords()

    def load_ingredients(self, api_data: dict):
        self.ingredients = api_data['ingredients']
        self.save()

    def load_total_size(self, api_data: dict):
        self.total_size = api_data['packageSize']
        self.save()

    def load_loblaws_nutrition_facts_json(self, loblaws_nutrition: dict):
        """
        Given LoblawsProduct.nutrition_facts_json field, will parse out all nutrients and dump data into this model
        """
        # Grab nutrients available in the NutritionFacts model
        nutritionfacts_model = NutritionFacts()
        nutrition_facts_attributes = list(vars(nutritionfacts_model))

        # Parse food labels (serving size, calories, calories from fat?).
        # Loop over and validate code to ensure we get the right data.
        if 'foodLabels' in loblaws_nutrition:
            for item in loblaws_nutrition['foodLabels']:
                if item['code'] == 'perservesizeamt':
                    self.serving_size_raw = item['valueInGram'].strip()
                    self.serving_size_units = self.__detect_units(self.serving_size_raw.lower())
                if item['code'] == 'calories':
                    # This is the correct key; just seems to be a naming error in the API
                    try:
                        self.calories, unit = self.__extract_number_from_nutrient(item['valueInGram'])
                    except TypeError:
                        pass

        # Parse the nutrientsPerServing, micronutrients, and subNutrients sections. Flatten into a 1-D list.
        nutrient_json = loblaws_nutrition['nutrientsPerServing'] + loblaws_nutrition['micronutrients']
        for n in nutrient_json:
            if n['subNutrients'] is not None:
                nutrient_json += n['subNutrients']

        # Verify that expected nutrient keys are present, extract matching model values
        nutrient_error_detected = False
        if any(x in ('nutrientsPerServing', 'micronutrients') for x in loblaws_nutrition):
            for n in nutrient_json:
                nutrient = n['code']
                if nutrient in nutrition_facts_attributes:  # Attributes for the NutritionFacts model
                    # Actual nutrient value
                    if n['valueInGram']:
                        try:
                            val, unit = self.__extract_number_from_nutrient(n['valueInGram'])
                            setattr(self, nutrient, val)
                        except TypeError as e:
                            nutrient_error_detected = True

                    # Percent DV
                    if n['valuePercent']:
                        try:
                            val, unit = self.__extract_number_from_nutrient(n['valuePercent'])
                            if unit != '%':
                                # print(f'Error detected for percent DV of {nutrient} -> found {val, unit}. '
                                #       f'Setting values to null.')
                                val, unit = None, None
                            setattr(self, (nutrient + '_dv'), val)
                        except TypeError as e:
                            nutrient_error_detected = True

        if nutrient_error_detected:
            print(f'Detected an error for {self.product} when parsing nutrition facts')

        self.save()

    @staticmethod
    def __detect_units(val: str) -> Optional[str]:
        """
        Method to detect units in a nutrient value string. Expects .lower() to be calleded on the input value already

        TODO: This is a super fragile implementation. The order of the if statements is very important, and there is
            some sketchy implicit logic that isn't clear, e.g. `if 'k' in val` covers both 'kCal' and 'k', and will
            then split on 'k' to extract the numeric value

        :param val: string for nutrient value e.g. 30 g, 50 cal, 500 mg,  etc.
        :return: string containing units for input value - this is the value that will be split on when extracting
                numeric values
        """
        if any(x in ['<', '>', '<=', '>='] for x in val):  # This junk shows up on rare occasions - ignore it
            return None
        # Milligrams
        elif 'mg' in val:
            return 'mg'
        elif 'milligrams' in val:
            return 'milligrams'
        # mL / millilitres
        elif 'ml' in val:
            return 'ml'
        elif 'millilitres' in val:
            return 'millilitres'
        # calories / cal
        elif 'k' in val:
            return 'k'
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
        elif 'l' in val or 'litres' in val:
            return 'l'
        else:
            # print(f"WARNING: Could not detect any units in value ({val})")
            return None

    def __extract_number_from_nutrient(self, val: str) -> Union[tuple, None]:
        """
        Given an input nutrient string, will return the float value while handling unit conversion if necessary
        """
        if val is None:
            return None

        # Check to see if the units are missing, but there is a numeric value. Just toss the data in this case.
        if val.isnumeric():
            return None

        # Grab the units from the nutrient string
        val = val.lower()
        nutrient_type = self.__detect_units(val)
        if nutrient_type is None:
            return None

        # Grab the numeric float value from the string
        try:
            nutrient_float = float(val.split(nutrient_type)[0].strip())
        except ValueError as e:  # If this fails it means the nutrient string is junk
            return None

        # Grams & Milligrams (normalizes everything into grams)
        if nutrient_type == 'g':
            return nutrient_float, 'g'
        elif nutrient_type == 'mg' or nutrient_type == "milligrams":
            return self.__convert_milligrams_to_grams(nutrient_float), 'g'

        # Percent DV (values on nutrition labels are integers ranging from 0% -> n%, so we convert to float)
        if nutrient_type == "dv" or nutrient_type == "%":
            return float(nutrient_float / 100), '%'

        # Calories
        if nutrient_type == "cal" or nutrient_type == "calories" or nutrient_type == "k":
            return int(nutrient_float), 'cal'
        return None

    @staticmethod
    def __convert_milligrams_to_grams(val: float) -> float:
        return val * 0.001

    @staticmethod
    def __valid_nutrient(nutrient: str) -> bool:
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
    """
    Extension of the generic Product model to store Loblaws specific metadata
    """

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="loblaws_product")
    upc_list = ArrayField(models.CharField(max_length=MD_CHAR), blank=True, null=True)

    # This JSON data is retrieved from the Loblaws API
    api_data = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Loblaws Product'
        verbose_name_plural = 'Loblaws Products'
        indexes = [
            models.Index(fields=['product'])
        ]

    history = HistoricalRecords()


# WALMART MODELS

class WalmartProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Walmart specific metadata
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="walmart_product")
    image_directory = models.CharField(max_length=MD_CHAR, blank=True, null=True)

    sku = models.CharField(max_length=SM_CHAR, blank=True, null=True)
    bullets = models.TextField(blank=True, null=True)
    dietary_info = models.TextField(blank=True, null=True)  # Corresponds to "Lifestyle and Dietary Need" in JSON
    nutrition_facts_json = JSONField(blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Walmart Product'
        verbose_name_plural = 'Walmart Products'


# GROCERY GATEWAY MODELS

class GroceryGatewayProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Grocery Gateway specific metadata
    """

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="grocerygateway_product")
    image_directory = models.CharField(max_length=MD_CHAR, blank=True, null=True)

    sku = models.CharField(max_length=SM_CHAR, blank=True, null=True)
    bullets = models.TextField(blank=True, null=True)
    dietary_info = models.TextField(blank=True, null=True)  # Corresponds to "Lifestyle and Dietary Need" in JSON
    nutrition_facts_json = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Grocery Gateway Product'
        verbose_name_plural = 'Grocery Gateway Products'
        indexes = [
            models.Index(fields=['product'])
        ]

    history = HistoricalRecords()


# VOILA MODELS
class VoilaProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Voila specific metadata
    """

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="voila_product")
    image_directory = models.CharField(max_length=MD_CHAR, blank=True, null=True)

    sku = models.CharField(max_length=SM_CHAR, blank=True, null=True)
    bullets = models.TextField(blank=True, null=True)
    dietary_info = models.TextField(blank=True, null=True)  # Corresponds to "Lifestyle and Dietary Need" in JSON
    nutrition_facts_json = JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Voila Product'
        verbose_name_plural = 'Voila Products'
        indexes = [
            models.Index(fields=['product'])
        ]

    history = HistoricalRecords()


# AMAZON MODELS

class AmazonProduct(TimeStampedModel):
    """
    Extension of the generic Product model to store Amazon specific metadata
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="amazon_product")
    bullet_points = models.TextField(null=True, blank=True)  # The Amazon description field
    manufacturer_reference = models.CharField(max_length=MD_CHAR, blank=True,
                                              null=True)  # e.g. from Amazon technical details
    speciality = models.CharField(max_length=MD_CHAR, blank=True, null=True)  # e.g. Kosher
    units = models.CharField(max_length=SM_CHAR, blank=True, null=True)  # e.g. 2.5 Kilograms
    item_weight = models.CharField(max_length=SM_CHAR, blank=True, null=True)  # e.g. 1.58 kg
    parcel_dimensions = models.CharField(max_length=SM_CHAR, blank=True, null=True)  # e.g. 30 x 30 x 30 cm
    date_first_available = models.DateField(null=True, blank=True)  # from the Additional Information table
    image_directory = models.CharField(max_length=LG_CHAR, blank=True, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"{self.product.product_code}: {self.product.name}"

    class Meta:
        verbose_name = 'Amazon Product'
        verbose_name_plural = 'Amazon Products'


class AmazonSearchResult(TimeStampedModel):
    """
    Stores information on the search page that a particular product showed up on
    """
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_search_result")
    search_string = models.CharField(max_length=MD_CHAR)  # Search string used to generate results
    page = models.IntegerField()  # Page that the product showed up on
    item_number = models.IntegerField()  # Of products shown on search page, tracks the index of the product (i.e. 2nd)

    class Meta:
        verbose_name = 'Amazon Search Result'
        verbose_name_plural = 'Amazon Search Results'


class AmazonProductReview(TimeStampedModel):
    """
    Model to store information on a single Amazon product review
    """
    # One Amazon Product will have many reviews
    product = models.ForeignKey(AmazonProduct, on_delete=models.CASCADE, related_name="amazon_product_reviews")
    review_title = models.CharField(max_length=MD_CHAR)
    review_text = models.TextField(blank=True, null=True)
    reviewer_username = models.CharField(max_length=SM_CHAR)
    rating = models.FloatField()  # e.g. 3 out of 5 stars -> convert to float
    helpful = models.BooleanField()  # Flag for if the review was marked as helpful or not by Amazon

    class Meta:
        verbose_name = 'Amazon Product Review'
        verbose_name_plural = 'Amazon Product Reviews'


# IMAGE CLASSIFICATION
class ProductImage(TimeStampedModel):
    """
    Model to store relationship between a Product and a path to a product image
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_image")
    image_path = models.ImageField(upload_to=upload_product_image, unique=True, max_length=LG_CHAR)
    image_number = models.IntegerField(blank=True, null=True)  # Order of the image in a set for a product
    image_label = models.CharField(max_length=SM_CHAR, null=True,
                                   blank=True)  # e.g. 'other', 'nutrition', 'ingredients'

    def __str__(self):
        return f"{self.product}: {Path(self.image_path.url).name}"

    @property
    def image_string(self):
        return self.image_path.url

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'


class NutritionLabelClassification(TimeStampedModel):
    """
    Stores output from the nutrition label classifier for a ProductImage
    """
    # Required fields
    product_image = models.ForeignKey(ProductImage, on_delete=models.CASCADE, related_name="image_classification")

    # Classification can be populated after the fact as it can take time to calculate
    classification_choices = (
        ('N', 'NUTRITION'),
        ('I', 'INGREDIENTS'),
        ('O', 'OTHER'),
    )
    classification = models.CharField(choices=classification_choices, max_length=SM_CHAR, null=True, blank=True)

    class Meta:
        verbose_name = 'Image Classification'
        verbose_name_plural = 'Image Classifications'


class FrontOfPackLabel(TimeStampedModel):
    """
    Stores output from the FrontOfPackLabel classifier
    """
    product_image = models.OneToOneField(ProductImage, on_delete=models.CASCADE, related_name="fop_label")

    # Results from the classifier should be available in a simple JSON object
    classifier_result_json = JSONField(blank=True, null=True)

    # Boolean to represent if a FOP label is present or not
    label_detected = models.BooleanField()

    # TODO: Figure out what kind of classifications we can nail down with the model
    label_type_choices = (
        ('FC', 'FOOD_COLOURING'),
    )
    label_type = models.CharField(max_length=SM_CHAR, choices=label_type_choices, null=True, blank=True)
    classified_image_path = models.ImageField(upload_to=upload_fop_image, max_length=LG_CHAR)

    def __str__(self):
        return f"{self.product_image.product.name} - FOP Present: {self.label_detected}"

    @property
    def classified_image_filename(self):
        return Path(self.classified_image_path.path).name

    class Meta:
        verbose_name = 'FOP Label'
        verbose_name_plural = 'FOP Labels'
