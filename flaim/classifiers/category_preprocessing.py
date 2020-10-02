import pandas as pd

from flaim.database.product_mappings import REFERENCE_SUBCATEGORIES_CODING_DICT, REFERENCE_CATEGORIES_CODING_DICT, \
    FLIP_TO_FLAIME_CONVERSION_DICT


class DataStore:
    def __init__(self):
        self.df = None
        self.product_ids = None
        self.names = None
        self.ingredients = None
        self.target = None
        self.subtarget = None

    def preprocess(self, process_names=True, process_ingredients=False):
        self.names = self.df.pop('name')
        self.ingredients = self.df.pop('ingredients')

        columns = ['calories', 'sodium', 'calcium_dv', 'totalfat', 'saturatedfat', 'transfat', 'totalcarbohydrate',
                   'dietaryfiber', 'sugar', 'protein', 'cholesterol', 'vitamina_dv', 'vitaminc_dv', 'iron_dv']
        self.df = self.df[columns]


class FLIP(DataStore):
    def __init__(self, path, target='TRA_Cat_2', subtarget='TRA_Item_2016'):
        super().__init__()

        self.df = pd.read_excel(path)
        self.df.columns = [FLIP_TO_FLAIME_CONVERSION_DICT[c]
                           if c in FLIP_TO_FLAIME_CONVERSION_DICT else c for c in self.df.columns]
        self.target = self.df.pop(target).map(REFERENCE_CATEGORIES_CODING_DICT)
        self.subtarget = self.df.pop(subtarget).str.replace('\.1', '')
        self.subtarget = (self.subtarget.str[0] + '.' + self.subtarget.str[1:]).map(REFERENCE_SUBCATEGORIES_CODING_DICT)
        self.flip_preprocess()

    def flip_preprocess(self):
        # flip has these columns in different units
        self.df['sodium'] /= 1000
        self.df['calcium_dv'] /= 100
        self.df['cholesterol'] /= 100
        self.df['vitamina_dv'] /= 100
        self.df['vitaminc_dv'] /= 100
        self.df['iron_dv'] /= 100

        super().preprocess()


class FLAIME(DataStore):
    def __init__(self, products=None, nutrition_facts=None, most_recent_bool=True):
        super().__init__()
        if products is not None and nutrition_facts is not None:
            if most_recent_bool:
                product_df = pd.DataFrame(list(products.objects.filter(most_recent=True).values()))
                nft_df = pd.DataFrame(list(nutrition_facts.objects.filter(product__most_recent=True).values()))
            else:
                product_df = pd.DataFrame(list(products.objects.all().values()))
                nft_df = pd.DataFrame(list(nutrition_facts.objects.all().values()))
            self.df = product_df.merge(nft_df, left_on='id', right_on='product_id')
            self.product_ids = product_df['id']
            self.preprocess()

    # local data for testing
    def get_sample_data(self):
        product_df = pd.read_csv('data/git_flaime_products.csv')
        nft_df = pd.read_csv('data/git_flaime_nutrition_facts.csv')
        self.df = product_df.merge(nft_df, left_on='id', right_on='product_id')
        self.preprocess()
