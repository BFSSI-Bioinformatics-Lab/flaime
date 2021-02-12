from functools import partial
from operator import is_not

import numpy as np
import pandas as pd


def nutrient_color(value):
    return 'text-success' if value <= 0.15 else 'text-danger'


def make_list(x):
    return list(filter(partial(is_not, np.nan), list(x)))


def rank_suffix(i):
    i = i + 1
    if i >= 11 and 11 <= int(str(i)[-2:]) <= 13:
        return f'{i}th'
    remainder = i % 10
    if remainder == 1:
        return f'{i}st'
    elif remainder == 2:
        return f'{i}nd'
    elif remainder == 3:
        return f'{i}rd'
    else:
        return f'{i}th'


def build_top_x_sentence(s: pd.Series, x):
    if x > s.nunique():
        x = s.nunique()
    common_categories = s.value_counts().head(x).to_dict()
    if x == 1:
        return f'{s.unique()} ({common_categories[s.unique()]} products)'
    sen = ', '.join([f'{key} ({common_categories[key]} products)' for key in common_categories])
    sen_par = sen.rpartition(', ')
    return sen_par[0] + ', and ' + sen_par[-1]


# This gets the 3 most common ingredients but does not preprocess the ingredient lists
def build_top_ingredient_sentence(ingredients: pd.Series):
    common_ingredients = pd.Series(' '.join(ingredients.fillna('').str.lower().tolist())
                                   .split(',')).value_counts().head(3).index.tolist()
    if len(common_ingredients) >= 3:
        return f'The three most common ingredients in this category are \
                {common_ingredients[0]}, {common_ingredients[1]}, and {common_ingredients[2]}.'
    elif len(common_ingredients) == 2:
        return f'The two most common ingredients in this category are \
                {common_ingredients[0]} and {common_ingredients[1]}.'
    # Seems unlikely to only have one ingredient, note it can still have 0 ingredients in which case this sentence
    # will not be displayed
    elif len(common_ingredients) == 1:
        return f'The only ingredient in this category is {common_ingredients[0]}.'
