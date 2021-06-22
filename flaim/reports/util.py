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


def preprocess_ingredients(ingredients: pd.Series):
    # gets rid of the stuff after the first period (usually allergy info etc.) if there is one
    step1 = ingredients.dropna().str.lower().str.extract(r'^(.*?)(\.|$)')[0]

    # removes things in parenthesis since they look generally low value
    # TODO: add [], remove space from regex
    step2 = step1.str.replace(r'( \(.*?\))', '', regex=True)

    # replaces and/or, & with commas (creates two items but might want to remove the second instead)
    # TODO: &/or, '/'
    step3 = step2.str.replace(r'(\s(?:(?:(?:and)|(?:or))\s?/?\s?(?:or)?|&)\s)', ', ', regex=True)

    # remove 'ingredients:'
    # TODO: remove 'x:' at the beginning
    step4 = step3.str.replace(r'(ingredients:\s?)', '', regex=True)

    # handle • as separator and period (second case gets filtered by step 1)
    step5 = step4.str.replace(r'( • )', ', ', regex=True)

    # remove footnote markers *, †, ¹, etc.
    # TODO: * prefix
    step6 = step5.str.replace(r'([^a-z]*,)', ', ', regex=True)

    # remove "x%" (% may not be there)
    # remove lists after ':'
    # remove "contains less than 2% of"

    return step6.fillna('')
