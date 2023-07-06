# Generated by Django 3.1.6 on 2022-07-18 12:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('database', '0036_auto_20220516_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalnutritionfacts',
            name='ingredients_french',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nutritionfacts',
            name='ingredients_french',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='HistoricalCostcoProduct',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, editable=False)),
                ('modified', models.DateTimeField(blank=True, editable=False)),
                ('image_directory', models.CharField(blank=True, max_length=500, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='database.product')),
            ],
            options={
                'verbose_name': 'historical Costco Product',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='CostcoProduct',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('image_directory', models.CharField(blank=True, max_length=500, null=True)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='costco_product', to='database.product')),
            ],
            options={
                'verbose_name': 'Costco Product',
                'verbose_name_plural': 'Costco Products',
            },
        ),
        migrations.AddIndex(
            model_name='costcoproduct',
            index=models.Index(fields=['product'], name='database_co_product_e0f909_idx'),
        ),
    ]