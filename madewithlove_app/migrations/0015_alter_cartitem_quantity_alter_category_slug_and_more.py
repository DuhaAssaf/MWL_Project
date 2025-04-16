# Generated by Django 5.1.7 on 2025-04-16 01:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('madewithlove_app', '0014_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='quantity',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.CharField(choices=[('fashion', 'Fashion & Apparel'), ('electronics', 'Electronics & Gadgets'), ('beauty', 'Beauty & Personal Care'), ('handmade', 'Handmade & Crafts'), ('food', 'Food & Specialty'), ('books', 'Books & Stationery'), ('home', 'Home & Kitchen'), ('local', 'Local & Cultural'), ('other', 'Other')], default='other', max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='message',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(10)]),
        ),
        migrations.AlterField(
            model_name='discount',
            name='percentage',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)]),
        ),
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator(message='Enter a valid phone number.', regex='^\\+?\\d{7,15}$')]),
        ),
    ]
