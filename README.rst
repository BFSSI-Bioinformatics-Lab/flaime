FLAIME
======

.. image:: https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg
     :target: https://github.com/pydanny/cookiecutter-django/
     :alt: Built with Cookiecutter Django
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
     :target: https://github.com/ambv/black
     :alt: Black code style


:License: MIT


Settings
--------

Moved to settings_.

.. _settings: http://cookiecutter-django.readthedocs.io/en/latest/settings.html

Basic Commands
--------------

Setting Up Your Users
^^^^^^^^^^^^^^^^^^^^^

* To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

Type checks
^^^^^^^^^^^

Running type checks with mypy:

::

  $ mypy flaim

Test coverage
^^^^^^^^^^^^^

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

Running tests with py.test
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  $ pytest

Sentry
^^^^^^

Sentry is an error logging aggregator service. You can sign up for a free account at  https://sentry.io/signup/?code=cookiecutter  or download and host it yourself.
The system is setup with reasonable defaults, including 404 logging and integration with the WSGI application.

You must set the DSN url in production.


Deployment
----------

**Dependencies:**
- Ubuntu 20.04
- PostgreSQL 12.2
- Python 3.7.6
- Node 14.8.0
- npm 6.14.7
- Redis

Additional dependencies can be found in `flaim/utility/requirements-bionic.apt`

Python dependencies can be found in `flaim/requirements/local.txt`

Run `npm i` to install necessary node packages.
Use `python manage.py collectstatic` to put them into the expected static directory.


Redis Guide
^^^^^^^^^^^
https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04
https://github.com/rq/django-rq


Installing Postgres Trigram Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We use this for more flexible searching. Installing this app on a new server will require this to be installed.

Trigrams allows you to do something like this::

    queryset = queryset.filter(name__trigram_similar=name_contains)


First, you must create an empty migration with the following command::

    python manage.py makemigrations database --empty

Then you must navigate to the newly created empty migration and set it up so it looks like this::


    from django.contrib.postgres.operations import TrigramExtension

    ...

    operations = [TrigramExtension()]

And confirm it with::

    python manage.py migrate


Misc. Dev Notes
^^^^^^^^^^^^^^^
If you're using fish, activate the venv with this command in the terminal::

    $ source venv/bin/activate.fish


To activate the browser based RQ dashboard::

    $ rq-dashboard



Using FLAIME
------------

Uploading new web scrapes
^^^^^^^^^^^^^^^^^^^^^^^^^
New data can be uploaded to the database via management commands available in `python manage.py`

To upload Walmart data:
`python manage.py load_walmart_to_db --input_dir /media/scraper_output/walmart/2020-08-19 --date 2020-08-19 `

To upload Loblaws data:
`python manage.py load_loblaws_to_db --input_dir /media/scraper_output/loblaws/2020-01-01 --date 2020-01-01 `

Once the data has been uploaded, it's important to predict categories on each new product. Eventually this will be
done automatically upon upload, though for now a single command must be called:
`python manage.py predict_product_categories`
