# Generated by Django 5.1.6 on 2025-04-10 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('madewithlove_app', '0003_customerprofile_phone_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
