# Generated by Django 3.0.7 on 2020-09-10 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0011_predictedcategory_manual_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryProductCodeMappingSupport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_code', models.CharField(max_length=500, unique=True)),
                ('category', models.CharField(choices=[('Baby Food', 'Baby Food'), ('Bakery Products', 'Bakery Products'), ('Beverages', 'Beverages'), ('Cereals and Other Grain Products', 'Cereals and Other Grain Products'), ('Combination Dishes', 'Combination Dishes'), ('Dairy Products and Substitutes', 'Dairy Products and Substitutes'), ('Desserts', 'Desserts'), ('Dessert Toppings and Fillings', 'Dessert Toppings and Fillings'), ('Eggs and Egg Substitutes', 'Eggs and Egg Substitutes'), ('Fats and Oils', 'Fats and Oils'), ('Fruit and Fruit Juices', 'Fruit and Fruit Juices'), ('Legumes', 'Legumes'), ('Marine and Fresh Water Animals', 'Marine and Fresh Water Animals'), ('Meal Replacements and Supplements', 'Meal Replacements and Supplements'), ('Meat and Poultry, Products and Substitutes', 'Meat and Poultry, Products and Substitutes'), ('Miscellaneous', 'Miscellaneous'), ('Nuts and Seeds', 'Nuts and Seeds'), ('Potatoes, Sweet Potatoes and Yams', 'Potatoes, Sweet Potatoes and Yams'), ('Salads', 'Salads'), ('Sauces, Dips, Gravies and Condiments', 'Sauces, Dips, Gravies and Condiments'), ('Snacks', 'Snacks'), ('Soups', 'Soups'), ('Sugars and Sweets', 'Sugars and Sweets'), ('Vegetables', 'Vegetables'), ('Not Food', 'Not Food')], max_length=500)),
            ],
        ),
    ]
