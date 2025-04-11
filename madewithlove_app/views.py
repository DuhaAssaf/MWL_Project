import bcrypt
from django.shortcuts import redirect, render
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils.http import urlencode
from .models import ProductImage, User, MerchantProfile, CustomerProfile, Subscription, Category
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

def homepage(request):
    return render(request, 'homepage.html')

def plans(request):
    plans = [
        {"name": "Basic", "price": "9", "features": ["1 Store", "10 Products", "Basic Support"], "cta": "Get Started"},
        {"name": "Pro", "price": "19", "features": ["3 Stores", "50 Products", "Priority Support"], "cta": "Choose Pro"},
        {"name": "Premium", "price": "29", "features": ["Unlimited Stores", "Unlimited Products", "24/7 Premium Support"], "cta": "Go Premium"},
    ]
    return render(request, 'plans.html', {"plans": plans})

def merchant_dashboard(request):
    return render(request, 'dashboard.html')

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
    user = request.user
    profile = MerchantProfile.objects.filter(user=user).first()

    if not profile:
        return redirect("dashboard")

    if request.method == "POST":
        profile.store_name = request.POST.get("store_name")
        profile.category_id = request.POST.get("category")
        profile.description = request.POST.get("description")
        profile.payout_method = request.POST.get("payout_method")
        profile.payout_email = request.POST.get("payout_email")
        profile.country = request.POST.get("country")
        profile.save()

        return redirect("dashboard")

    categories = Category.objects.all()
    return render(request, "merchant_setup_form.html", {
        "categories": categories,
        "profile": profile,
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

        # Hash password using bcrypt
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

        # Optionally, auto-login the user or set a success message
        request.session['user_id'] = user.id  # Simple session-based login (optional)

        # Redirect to appropriate dashboard
        if role == 'merchant':
            return redirect('merchant_dashboard')
        else:
            return redirect('customer_dashboard')

    return render(request, 'register.html')

def merchant_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')  # Redirect to login if not authenticated

    try:
        user = User.objects.get(id=user_id)
        if user.role != 'merchant':
            return redirect('customer_dashboard')

        merchant_profile = MerchantProfile.objects.filter(user=user).first()
        return render(request, 'dashboards/merchant_dashboard.html', {
            'user': user,
            'merchant_profile': merchant_profile,
        })
    except User.DoesNotExist:
        return redirect('login')
    

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
        identifier = request.POST.get('username')  # Username or email
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'

        user = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()

        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                # ✅ Set session info
                request.session['user_id'] = user.id
                request.session['username'] = user.username
                request.session['full_name'] = user.full_name
                request.session['role'] = user.role

                # ✅ Set profile picture URL
                default_url = '/static/img/default-profile.png'
                profile_url = None

                if user.role == 'merchant':
                    profile = MerchantProfile.objects.filter(user=user).first()
                    if profile and profile.profile_picture:
                        profile_url = profile.profile_picture.url
                elif user.role == 'customer':
                    profile = CustomerProfile.objects.filter(user=user).first()
                    if profile and profile.profile_picture:
                        profile_url = profile.profile_picture.url

                request.session['profile_picture_url'] = profile_url or default_url

                # ✅ Set session expiry
                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks
                else:
                    request.session.set_expiry(0)  # Session expires on browser close

                # ✅ Redirect based on role
                if user.role == 'merchant':
                    return redirect('merchant_dashboard')
                elif user.role == 'customer':
                    return redirect('explore')  # All stores page

            else:
                return render(request, 'login.html', {'error': 'Invalid password.'})
        else:
            return render(request, 'login.html', {'error': 'User not found.'})

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

        merchant = MerchantProfile.objects.filter(user_id=user_id).first()
        store = merchant.store

        product_id = request.POST.get('product_id')
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        images = request.FILES.getlist('images')

        if product_id:
            # Edit product
            product = Product.objects.get(id=product_id)
            product.name = name
            product.price = price
            product.stock = stock
            product.category_id = category_id
            product.description = description
            product.save()
        else:
            # Add new product
            product = Product.objects.create(
                store=store,
                name=name,
                price=price,
                stock=stock,
                category_id=category_id,
                description=description
            )

        if images:
            for img in images:
                ProductImage.objects.create(product=product, merchant=merchant, image=img)

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


