from django.contrib import admin
from .models import (
    User, Category, MerchantProfile, Store,
    Product, ProductImage, CustomerProfile,
    Order, OrderItem, Review, Notification,
    Discount, Subscription, RecentlyViewedProduct,CartItem
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email']
    list_filter = ['role', 'is_active', 'is_staff']
    ordering = ['-date_joined']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['slug']
    list_filter = ['slug']
    search_fields = ['slug']


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = [ 'user', 'country', 'is_profile_complete']
    list_filter = ['is_profile_complete', 'country']
    search_fields = [ 'user__username']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'merchant', 'category', 'is_store_active']
    list_filter = ['is_store_active', 'category']
    search_fields = ['name', 'merchant__store_name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'price', 'stock', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'store__name']
    ordering = ['-created_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image']
    search_fields = ['product__name']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'joined_at']
    search_fields = ['user__username', 'user__email']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'total_amount', 'created_at']
    list_filter = ['status']
    search_fields = ['customer__user__username']
    ordering = ['-created_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['order__id', 'product__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'created_at']
    search_fields = ['product__name', 'customer__user__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'percentage', 'is_active', 'valid_until']
    list_filter = ['is_active']
    search_fields = ['code']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan_name', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(RecentlyViewedProduct)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ['customer', 'product', 'viewed_at']
    search_fields = ['customer__user__username', 'product__name']
