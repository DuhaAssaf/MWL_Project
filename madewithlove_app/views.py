from ast import Store
import bcrypt
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils.http import urlencode
from .models import ProductImage, User, MerchantProfile, CustomerProfile, Subscription, Category,Store
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.text import slugify

def homepage(request):
    return render(request, 'homepage.html')

def plans(request):
    plans = [
        {"name": "Basic", "price": "9", "features": ["1 Store", "10 Products", "Basic Support"], "cta": "Get Started"},
        {"name": "Pro", "price": "19", "features": ["3 Stores", "50 Products", "Priority Support"], "cta": "Choose Pro"},
        {"name": "Premium", "price": "29", "features": ["Unlimited Stores", "Unlimited Products", "24/7 Premium Support"], "cta": "Go Premium"},
    ]
    return render(request, 'plans.html', {"plans": plans})

@login_required
def merchant_dashboard_view(request):
    user = request.user

    # Redirect if not a merchant
    if user.role != 'merchant':
        return redirect('home')

    # Get merchant profile and store
    profile = get_object_or_404(MerchantProfile.objects.select_related('store'), user=user)
    store = profile.store

    if not store:
        return render(request, 'dashboards/merchant_dashboard.html', {
            'profile': profile,
            'products': [],
            'categories': Category.objects.all(),
            'store_missing': True,
        })

    # Load store products and images
    products = Product.objects.filter(store=store).prefetch_related('images')

    context = {
        'profile': profile,
        'store': store,
        'products': products,
        'categories': Category.objects.all(),
        'store_missing': False,
    }

    return render(request, 'dashboards/merchant_dashboard.html', context)


def customer_dashboard(request):
    return HttpResponse("Welcome to the Customer Dashboard!")

def admin_dashboard(request):
    return HttpResponse("Welcome to the Admin Dashboard!")

def subscriptions(request):
    return render(request, 'subscriptions.html')

def explore(request):
    return render(request, 'explore.html')

@login_required
def merchant_setup_view(request):
    print("User:", request.user, "| Authenticated:", request.user.is_authenticated)

    user = request.user
    if not user.is_authenticated or user.role != 'merchant':
        return redirect('login')  # Prevent access for non-merchants

    profile, _ = MerchantProfile.objects.get_or_create(user=user)
    categories = Category.objects.all()
    error = None

    if request.method == 'POST':
        store_name = request.POST.get('store_name', '').strip()
        category_slug = request.POST.get('category')
        description = request.POST.get('description', '').strip()
        payout_method = request.POST.get('payout_method', '').strip()
        payout_email = request.POST.get('payout_email', '').strip()
        country = request.POST.get('country', '').strip()
        profile_picture = request.FILES.get('profile_picture')
        store_logo = request.FILES.get('store_logo')
        slug = slugify(store_name)

        # Validation
        if len(store_name) < 5:
            error = "Store name must be more than 5 characters."
        elif not category_slug:
            error = "Please select a category."
        elif len(description) < 15:
            error = "Description must be more than 15 characters."
        elif not payout_email:
            error = "Payout email is required."
        else:
            try:
                validate_email(payout_email)
            except ValidationError:
                error = "Enter a valid email address."

        category = Category.objects.filter(slug=category_slug).first()
        if not category and not error:
            error = "Selected category is invalid."

        if not error:
            # Create or update store
            if profile.store:
                store = profile.store
            else:
                store = Store()

            store.name = store_name
            store.description = description
            store.category = category
            store.slug = slug
            if store_logo:
                store.store_logo = store_logo
            store.save()

            # Link store to merchant profile
            profile.store = store
            profile.payout_method = payout_method
            profile.payout_email = payout_email
            profile.country = country
            profile.profile_picture = profile_picture if profile_picture else profile.profile_picture
            profile.is_profile_complete = True
            profile.save()

            return redirect('merchant_dashboard')

    return render(request, 'merchant-setup.html', {
        'categories': categories,
        'error': error,
        'profile': profile
    })

def contact(request):
    return render(request, 'contact.html')

def auth_page(request):
    return render(request, 'auth.html')

def merchant_profile_page(request):
    profile = {
        "store_name": "Handmade Creations",
        "category": "Crafts",
        "bio": "Beautiful handmade items for gifting and home decor.",
        "payment_provider": "PayPal",
        "payout_email": "merchant@example.com",
        "country": "Jordan",
        "id_upload": {"url": "https://via.placeholder.com/200x120"},
    }
    return render(request, 'merchant_profile.html', {"profile": profile})

from django.shortcuts import render, redirect
from .models import MerchantProfile, CustomerProfile, Product



def storefront_by_slug(request, slug):
    sample_stores = {
        "handmade-creations": {
            "store_name": "Handmade Creations",
            "store_description": "Beautiful handcrafted gifts and decor.",
            "products": [
                {"name": "Bracelet", "description": "Beaded charm bracelet", "price": "15.00", "image": "https://via.placeholder.com/300", "category": "Accessories"},
                {"name": "Notebook", "description": "Eco notebook", "price": "10.00", "image": "https://via.placeholder.com/300", "category": "Stationery"},
                {"name": "Gift Box", "description": "Holiday gift box", "price": "25.00", "image": "https://via.placeholder.com/300", "category": "Gifts"},
                {"name": "Mug", "description": "Handmade ceramic mug", "price": "12.00", "image": "https://via.placeholder.com/300", "category": "Homeware"},
                {"name": "Planner", "description": "Weekly planner", "price": "9.99", "image": "https://via.placeholder.com/300", "category": "Stationery"},
            ]
        }
    }

    store = sample_stores.get(slug)
    if not store:
        return render(request, '404.html', status=404)

    products = store["products"]
    store_name = store["store_name"]
    store_description = store["store_description"]

    search_query = request.GET.get("search", "").lower()
    category_filter = request.GET.get("category", "")
    page_number = request.GET.get("page", 1)

    if search_query:
        products = [p for p in products if search_query in p["name"].lower() or search_query in p["description"].lower()]
    if category_filter:
        products = [p for p in products if p["category"] == category_filter]

    categories = sorted(set(p["category"] for p in store["products"]))
    paginator = Paginator(products, 6)
    page_obj = paginator.get_page(page_number)

    context = {
        "store_name": store_name,
        "store_description": store_description,
        "products": page_obj,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_filter,
        "pagination_query": urlencode({"search": search_query, "category": category_filter}),
    }

    return render(request, "storefront.html", context)

def explore_all_stores(request):
    stores = [
        {"slug": "handmade-creations", "store_name": "Handmade Creations", "description": "Beautiful handcrafted gifts and decor.", "image": "https://via.placeholder.com/300"},
        {"slug": "digital-art-zone", "store_name": "Digital Art Zone", "description": "Prints and graphics by creative artists.", "image": "https://via.placeholder.com/300"},
        {"slug": "planner-heaven", "store_name": "Planner Heaven", "description": "Organizers, calendars and goal trackers.", "image": "https://via.placeholder.com/300"},
    ]
    return render(request, "explore.html", {"stores": stores})

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        full_name = request.POST.get('full_name').strip()
        role = request.POST.get('role')
        email = request.POST.get('email').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate fields
        if not all([username, full_name, role, email, password1, password2]):
            return render(request, 'register.html', {'error': 'All required fields must be filled out.'})

        if role not in ['merchant', 'customer']:
            return render(request, 'register.html', {'error': 'Invalid role selected.'})

        if password1 != password2:
            return render(request, 'register.html', {'error': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already taken.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Email already registered.'})

        # Hash password
        hashed_password = bcrypt.hashpw(password1.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create user
        user = User.objects.create(
            username=username,
            email=email,
            full_name=full_name,
            phone_number=phone_number,
            password=hashed_password,
            role=role,
        )

        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        # ✅ Set session
        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['full_name'] = user.full_name
        request.session['role'] = user.role

        default_url = '/static/img/default-profile.png'
        profile_url = None

        if role == 'merchant':
            # Create empty merchant profile if not exists
            profile, created = MerchantProfile.objects.get_or_create(user=user)
            if profile.profile_picture:
                profile_url = profile.profile_picture.url
            request.session['profile_picture_url'] = profile_url or default_url

            if not profile.is_profile_complete:
                return redirect('merchant_setup')
            return redirect('merchant_dashboard')

        elif role == 'customer':
            profile, created = CustomerProfile.objects.get_or_create(user=user)
            if profile.profile_picture:
                profile_url = profile.profile_picture.url
            request.session['profile_picture_url'] = profile_url or default_url
            return redirect('explore')

        return redirect('login')  # fallback

    return render(request, 'register.html')

def merchant_dashboard(request):
    return render(request,'dashboards/merchant_dashboard.html')    

def customer_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
        if user.role != 'customer':
            return redirect('merchant_dashboard')

        customer_profile = CustomerProfile.objects.filter(user=user).first()
        return render(request, 'dashboards/customer_dashboard.html', {
            'user': user,
            'customer_profile': customer_profile,
        })
    except User.DoesNotExist:
        return redirect('login')


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username')  # Username or Email
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'

        user = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # ✅ Set session values
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['full_name'] = user.full_name
            request.session['role'] = user.role

            # ✅ Handle profile picture
            default_url = '/static/img/default-profile.png'
            profile_url = None

            if user.role == 'merchant':
                profile = MerchantProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url

                request.session['profile_picture_url'] = profile_url or default_url

                # ✅ Merchant: check profile completion
                if not profile or not profile.is_profile_complete:
                    return redirect('merchant_setup')
                return redirect('merchant_dashboard')

            elif user.role == 'customer':
                profile = CustomerProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url

                request.session['profile_picture_url'] = profile_url or default_url
                return redirect('explore')

            elif user.role == 'admin':
                return redirect('/admin/')  # Optional: or use custom admin dashboard

            # Fallback (safety net)
            return redirect('login')

        # Invalid password or user not found
        error_message = 'Invalid password.' if user else 'User not found.'
        return render(request, 'login.html', {'error': error_message})

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

def add_or_edit_product(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        role = request.session.get('role')

        if role != 'merchant':
            return JsonResponse({'success': False, 'message': 'Unauthorized'})

        # Get merchant profile and store
        merchant = MerchantProfile.objects.filter(user_id=user_id).first()
        if not merchant or not merchant.store:
            return JsonResponse({'success': False, 'message': 'Merchant store not found'})

        store = merchant.store
        category = store.category  # Auto-assign category from store

        # Get product fields
        product_id = request.POST.get('product_id')
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        images = request.FILES.getlist('images')

        if not all([name, price, stock, description]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})

        # Add or update
        if product_id:
            product = Product.objects.filter(id=product_id, store=store).first()
            if not product:
                return JsonResponse({'success': False, 'message': 'Product not found'})

            product.name = name
            product.price = price
            product.stock = stock
            product.description = description
            product.category = category  # Always update to match store
            product.save()
        else:
            product = Product.objects.create(
                store=store,
                name=name,
                price=price,
                stock=stock,
                description=description,
                category=category  # Auto-filled
            )

        # Save product images
        if images:
            for img in images:
                ProductImage.objects.create(product=product, image=img)

        return JsonResponse({'success': True, 'message': 'Product saved successfully'})
    
@csrf_exempt
def delete_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = Product.objects.filter(id=product_id).first()
        if product:
            product.delete()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Product not found'})
    

def admin_dashboard_view(request):
    # Replace this with your actual logic
    return render(request, 'admin_dashboard.html')


