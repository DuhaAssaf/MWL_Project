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
    path('dashboard/merchant/', views.merchant_dashboard, name='merchant_dashboard'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path("dashboard/add-edit-product/", views.add_or_edit_product, name="add_product"),
    path('confirm-order/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    
    ]
