# FLAIME

## Settings

[Settings Documentation](http://cookiecutter-django.readthedocs.io/en/latest/settings.html)

## Setting Up Users

* To create an **superuser account**, use this command:

>python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

##  Running tests with pytest

Config for pytest is available in `pytest.ini`

Run tests:
>pytest

##  Deployment

**Dependencies:**
- Ubuntu 20.04
- PostgreSQL 12.2
- Python 3.7.6
- Node 14.8.0
- npm 6.14.7
- Redis

Additional dependencies can be found in `flaim/utility/requirements-bionic.apt`

Python dependencies can be found in `flaim/requirements/local.txt`

Note that while `nltk` is listed as a dependency, two additional packages must be installed via the Python shell for
category predictions to function correctly.

>python manage.py shell
```python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
```

Run `npm i` to install necessary node packages.
Use `python manage.py collectstatic` to put them into the expected static directory.


##  Redis Guide
[Installing Redis](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04
)
[Installing Django RQ](https://github.com/rq/django-rq)

##  Installing Postgres Trigram Extension
We use this for more flexible searching. Installing this app on a new server will require this to be installed.

Trigrams allows you to do something like this:

```python
queryset = queryset.filter(name__trigram_similar=name_contains)
```

First, you must create an empty migration with the following command::

>python manage.py makemigrations database --empty

Then you must navigate to the newly created empty migration and set it up so it looks like this::

```python
from django.contrib.postgres.operations import TrigramExtension

# ...

operations = [TrigramExtension()]
```

And confirm it with:

>python manage.py migrate


## Misc. Dev Notes

To activate the browser based RQ dashboard:

>rq-dashboard


##  Using FLAIME

### Uploading new web scrapes

New data can be uploaded to the database via management commands available in `python manage.py`

To upload Walmart data:
>python manage.py load_walmart_to_db --input_dir /media/scraper_output/walmart/2020-08-19 --date 2020-08-19

To upload Loblaws data:
>python manage.py load_loblaws_to_db --input_dir /media/scraper_output/loblaws/2020-01-01 --date 2020-01-01

Following upload of data, categories will be automatically predicted and assigned and Atwater calculations will be run.


### Export reports

Ad-hoc product reports can be generated using `manage.py export_product_report`

`python manage.py export_product_report --help`

```text
usage: manage.py export_product_report [-h] --outdir OUTDIR [--all_products]
                                       [--categories {Bakery Products,Beverages,Cereals and Other Grain Products,Dairy Products and Substitutes,Desserts,Eggs and Egg Substitutes,Fats and Oils,Marine and Fresh Water Animals,Fruit and Fruit Juices,Legumes,Meat and Poultry, Products and Substitutes,Miscellaneous,Combination Dishes,Nuts and Seeds,Potatoes, Sweet Potatoes and Yams,Salads,Sauces, Dips, Gravies and Condiments,Snacks,Soups,Sugars and Sweets,Vegetables,Baby Food,Meal Replacements and Nutritional Supplements,Not Food} [{Bakery Products,Beverages,Cereals and Other Grain Products,Dairy Products and Substitutes,Desserts,Eggs and Egg Substitutes,Fats and Oils,Marine and Fresh Water Animals,Fruit and Fruit Juices,Legumes,Meat and Poultry, Products and Substitutes,Miscellaneous,Combination Dishes,Nuts and Seeds,Potatoes, Sweet Potatoes and Yams,Salads,Sauces, Dips, Gravies and Condiments,Snacks,Soups,Sugars and Sweets,Vegetables,Baby Food,Meal Replacements and Nutritional Supplements,Not Food} ...]]

Export a full product report to a .csv file with ease. Can filter on a variety
of options.

optional arguments:
  -h, --help            show this help message and exit
  --outdir OUTDIR       Path to export reports
  --all_products        Sets most_recent=False when filtering the product set.
                        Beware, this will make the script run considerably
                        slower.
  --categories          Filter queryset to only the specified categories. Can
                        take multiple categories at once, delimited by a space
                        e.g. --categories "Soups" "Beverages" will filter the
                        queryset to only contain products from the Soups and
                        Beverages categories.
```
