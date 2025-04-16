from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.homepage, name='home'),
    path('plans/', views.plans, name='plans'),
    path("merchant/setup/", views.merchant_setup_view, name="merchant_setup"),
    path('contact/', views.contact, name='contact'),
    path('merchant/profile/', views.merchant_profile_page, name='merchant_profile'),
    path('store/<slug:slug>/', views.storefront_by_slug, name='storefront_by_slug'),
    path("explore/", views.explore_all_stores, name="explore"),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/merchant/', views.merchant_dashboard_view, name='merchant_dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path("dashboard/add-edit-product/", views.add_or_edit_product, name="add_product"),
    path("dashboard/products/json/", views.get_merchant_products, name="merchant_products_json"),
    path('add-to-cart/', views.add_to_cart_dynamic, name='add_to_cart_dynamic'),
    path('customer/setup/', views.create_customer_profile, name='create_customer_profile'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('customer/profile/edit/', views.edit_customer_profile, name='edit_customer_profile'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('merchant/contact/<int:store_id>/', views.contact_merchant, name='contact_merchant'),
    path('cart/download/<int:store_id>/', views.download_cart_pdf, name='download_cart_pdf'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path("api/product/<int:product_id>/image/", views.product_image_api, name="product_image_api"),
    path('contact/', views.contact, name='contact'),
    path('ajax/contact/', views.ajax_contact, name='ajax_contact'),
    path('superadmin/', views.internal_admin_dashboard, name='internal_admin_dashboard'),
    path('superadmin/user/<int:user_id>/edit/', views.edit_user_view, name='edit_user'),
    path('superadmin/user/<int:user_id>/delete/', views.delete_user_view, name='delete_user'),
    path('superadmin/store/<int:store_id>/edit/', views.edit_store_view, name='edit_store'),
    path('superadmin/store/<int:store_id>/delete/', views.delete_store_view, name='delete_store'),
    path('superadmin/product/<int:product_id>/edit/', views.edit_product_view, name='edit_product'),
    path('superadmin/product/<int:product_id>/delete/', views.delete_product_view, name='delete_product'),
    path('superadmin/cart-item/<int:item_id>/edit/', views.edit_cart_item, name='edit_cart_item'),
    path('superadmin/cart-item/<int:item_id>/delete/', views.delete_cart_item, name='delete_cart_item'),



    ]
