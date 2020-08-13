import pandas as pd


class DataStore:
    def __init__(self):
        self.df = None
        self.product_ids = None
        self.names = None
        self.ingredients = None
        self.target = None

    def preprocess(self, process_names=True, process_ingredients=False):
        self.names = self.df.pop('name')
        self.ingredients = self.df.pop('ingredients')

        columns = ['calories', 'sodium', 'calcium_dv', 'totalfat', 'saturatedfat', 'transfat', 'totalcarbohydrate_dv',
                   'dietaryfiber', 'sugar', 'protein', 'cholesterol', 'vitamina_dv', 'vitaminc_dv', 'iron_dv']
        self.df = self.df[columns]


class FLIP(DataStore):
    def __init__(self, path):
        super().__init__()

        category_map = {'A': 'Bakery Products', 'B': 'Beverages', 'C': 'Cereals and Other Grain Products',
                        'D': 'Dairy Products and Substitutes', 'E': 'Desserts', 'F': 'Dessert Toppings and Fillings',
                        'G': 'Eggs and Egg Substitutes', 'H': 'Fats and Oils', 'I': 'Marine and Fresh Water Animals',
                        'J': 'Fruit and Fruit Juices', 'K': 'Legumes',
                        'L': 'Meat and Poultry, Products and Substitutes',
                        'M': 'Miscellaneous', 'N': 'Combination Dishes', 'O': 'Nuts and Seeds',
                        'P': 'Potatoes, Sweet Potatoes and Yams', 'Q': 'Salads',
                        'R': 'Sauces, Dips, Gravies and Condiments', 'S': 'Snacks', 'T': 'Soups',
                        'U': 'Sugars and Sweets', 'V': 'Vegetables', 'W': 'Baby Food',
                        'X': 'Meal Replacements and Supplements'}

        conversion_map = {'Product Name': 'name', 'Ingredients': 'ingredients', 'KCAL': 'calories', 'FAT': 'totalfat',
                          'FAT_%DV': 'totalfat_dv', 'SATFAT': 'saturatedfat', 'SATFAT_%DV': 'saturatedfat_dv',
                          'TRANS': 'transfat', 'CHOL': 'cholesterol', 'NA': 'sodium', 'NA_%DV': 'sodium_dv',
                          'CHO': 'totalcarbohydrate_dv', 'FIBRE': 'dietaryfiber', 'SUGAR': 'sugar', 'PRO': 'protein',
                          'VITA%': 'vitamina_dv', 'VITC%': 'vitaminc_dv', 'CALCIUM%': 'calcium_dv', 'IRON%': 'iron_dv'}

        self.df = pd.read_excel(path)
        self.df.columns = [conversion_map[c] if c in conversion_map else c for c in self.df.columns]
        self.target = self.df.pop('TRA_Cat_2').map(category_map)
        self.flip_preprocess()

    def flip_preprocess(self):
        # flip has these columns in different units
        self.df['sodium'] /= 1000
        self.df['calcium_dv'] /= 100
        self.df['totalcarbohydrate_dv'] /= 100
        self.df['cholesterol'] /= 100
        self.df['vitamina_dv'] /= 100
        self.df['vitaminc_dv'] /= 100
        self.df['iron_dv'] /= 100

        super().preprocess()


class FLAIME(DataStore):
    def __init__(self, products=None, nutrition_facts=None):
        super().__init__()
        if products is not None and nutrition_facts is not None:
            product_df = pd.DataFrame(list(products.objects.filter(most_recent=True).values()))
            nft_df = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True).values()))
            self.df = product_df.merge(nft_df, left_on='id', right_on='product_id')
            self.product_ids = product_df['id']
            self.preprocess()

    # local data for testing
    def get_sample_data(self):
        product_df = pd.read_csv('data/git_flaime_products.csv')
        nft_df = pd.read_csv('data/git_flaime_nutrition_facts.csv')
        self.df = product_df.merge(nft_df, left_on='id', right_on='product_id')
        self.preprocess()
