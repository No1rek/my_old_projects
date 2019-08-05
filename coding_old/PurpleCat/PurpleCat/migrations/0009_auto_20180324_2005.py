# Generated by Django 2.0.3 on 2018-03-24 18:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('PurpleCat', '0008_auto_20180324_1848'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='image',
            field=models.ImageField(upload_to='media/uploads/'),
        ),
        migrations.AlterField(
            model_name='image',
            name='url',
            field=models.CharField(blank=True, default='media/uploads/', max_length=256),
        ),
        migrations.AlterField(
            model_name='post',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='PurpleCat.User'),
        ),
        migrations.AlterField(
            model_name='post',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='PurpleCat.Category'),
        ),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='PurpleCat.Image'),
        ),
    ]
