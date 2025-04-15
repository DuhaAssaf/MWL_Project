from django.urls import include, path
from . import views
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from .views import ajax_contact_view



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
    path('subscribe/', views.subscribe_view, name='subscribe'),
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('contact/', views.contact, name='contact'),
    path('ajax/contact/', views.ajax_contact_view, name='ajax_contact'),



    ]
