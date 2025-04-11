from django.contrib import admin
from .models import (
    User, MerchantProfile, CustomerProfile, Store,
    Product, ProductImage, Category, Order, OrderItem,
    Review, Notification, Discount, Subscription, RecentlyViewedProduct
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'date_joined')
    list_filter = ('role',)
    search_fields = ('username', 'email', 'full_name')


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'country', 'created_at')
    list_filter = ('country',)
    search_fields = ('store_name', 'user__username')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'joined_at')
    search_fields = ('user__username',)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('merchant__store_name', 'slug')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'store', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('is_active', 'category')
    search_fields = ('name', 'store__merchant__store_name')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'merchant')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    search_fields = ('customer__user__username',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer', 'rating', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('user__username',)


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage', 'is_active', 'valid_until')
    list_filter = ('is_active',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'plan_name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(RecentlyViewedProduct)
class RecentlyViewedProductAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'viewed_at')
    search_fields = ('customer__user__username', 'product__name')
