# Generated by Django 2.0.3 on 2018-03-22 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('PurpleCat', '0004_category_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='link',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=64),
        ),
    ]
