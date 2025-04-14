from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # works with Django auth
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('merchant', 'Merchant'),
        ('customer', 'Customer'),
    ]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = CustomUserManager()

    def __str__(self):
        return self.username

class Category(models.Model):
    CATEGORY_CHOICES = [
            ('fashion', 'Fashion & Apparel'),
            ('electronics', 'Electronics & Gadgets'),
            ('beauty', 'Beauty & Personal Care'),
            ('handmade', 'Handmade & Crafts'),
            ('food', 'Food & Specialty'),
            ('books', 'Books & Stationery'),
            ('home', 'Home & Kitchen'),
            ('local', 'Local & Cultural'),
            ('other','other'),
        ]

    slug = models.CharField(max_length=50, unique=True, choices=CATEGORY_CHOICES, default='other')

    def __str__(self):
        return dict(self.CATEGORY_CHOICES).get(self.slug, self.slug)

class MerchantProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    payout_method = models.CharField(max_length=50,null=True,blank=True)
    payout_email = models.EmailField()
    country = models.CharField(max_length=100)
    is_profile_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    store = models.OneToOneField(
        'Store',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='merchant'
    )


    def __str__(self):
        return self.country
    
class Store(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(unique=True,null=True)
    is_store_active = models.BooleanField(default=True)
    store_logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    store=models.ForeignKey(Store, on_delete=models.CASCADE, related_name='product', null=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.name}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # Add this line
    address = models.TextField(blank=True, null=True)
    wishlist = models.ManyToManyField(Product, blank=True, related_name='wishlisted_by')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class RecentlyViewedProduct(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        recent = RecentlyViewedProduct.objects.filter(customer=self.customer).order_by('-viewed_at')
        if recent.count() > 10:
            for extra in recent[10:]:
                extra.delete()

    def __str__(self):
        return f"{self.customer.user.username} viewed {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.TextField()

    def __str__(self):
        return f"Order #{self.pk} - {self.customer.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.customer.user.username} on {self.product.name}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


class Discount(models.Model):
    code = models.CharField(max_length=20, unique=True)
    percentage = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    valid_until = models.DateTimeField()

    def __str__(self):
        return f"{self.code} - {self.percentage}%"


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    plan_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"



class CartItem(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('customer', 'product')  # Prevent duplicate cart entries for same product

    def __str__(self):
        return f"{self.customer.user.username} - {self.product.name} ({self.quantity})"