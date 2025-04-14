from ast import Store
import bcrypt
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils.http import urlencode
from .models import ProductImage, User, MerchantProfile, CustomerProfile, Subscription, Category,Store,Order,OrderItem
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.db.models import Prefetch


def homepage(request):
    return render(request, 'homepage.html')

def plans(request):
    plans = [
        {"name": "Basic", "price": "9", "features": ["1 Store", "10 Products", "Basic Support"], "cta": "Get Started"},
        {"name": "Pro", "price": "19", "features": ["3 Stores", "50 Products", "Priority Support"], "cta": "Choose Pro"},
        {"name": "Premium", "price": "29", "features": ["Unlimited Stores", "Unlimited Products", "24/7 Premium Support"], "cta": "Go Premium"},
    ]
    return render(request, 'plans.html', {"plans": plans})

def merchant_profile_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'merchant':
            profile_exists = MerchantProfile.objects.filter(user=request.user).exists()
            if not profile_exists:
                return redirect('create_merchant_profile')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@merchant_profile_required
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

def explore_all_stores(request):
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
 
    # Prefetch products with images, only active ones
    active_products = Prefetch(
        "product",
        queryset=Product.objects.filter(is_active=True).prefetch_related("images"),
        to_attr="products"
    )
 
    stores = Store.objects.filter(is_store_active=True).select_related("category").prefetch_related(active_products)
 
    if query:
        stores = stores.filter(name__icontains=query)
 
    paginator = Paginator(stores, 6)  # Show 6 stores per page
    page_obj = paginator.get_page(page)
 
    user = request.user if request.user.is_authenticated else None
    role = getattr(user, 'role', None)
 
    user_store_id = None
    if role == "merchant":
        merchant = MerchantProfile.objects.filter(user=user).first()
        if merchant and merchant.store:
            user_store_id = merchant.store.id
 
    context = {
        "stores": page_obj,
        "query": query,
        "role": role,
        "user_store_id": user_store_id,
        "page_obj": page_obj,
        "product":Product.objects.all()
    }
 
    return render(request, "explore.html", context)

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
    store = get_object_or_404(Store, slug=slug, is_store_active=True)
   
    # Get active products + related images
    products_qs = Product.objects.filter(store=store, is_active=True).prefetch_related("images")
 
    search_query = request.GET.get("search", "").strip().lower()
    category_filter = request.GET.get("category", "").strip()
    page_number = request.GET.get("page", 1)
 
    if search_query:
        products_qs = products_qs.filter(name__icontains=search_query)
 
    if category_filter:
        products_qs = products_qs.filter(category__slug=category_filter)
 
    # Get all categories used in this store's products
    store_categories = Category.objects.filter(product__store=store).distinct()
 
    paginator = Paginator(products_qs, 6)
    page_obj = paginator.get_page(page_number)
 
    # Prepare role info
    user = request.user if request.user.is_authenticated else None
    role = getattr(user, 'role', None)
    user_store_id = None
    if role == "merchant":
        merchant = MerchantProfile.objects.filter(user=user).first()
        if merchant and merchant.store:
            user_store_id = merchant.store.id
 
    # Prepare product data with image URLs
    product_list = []
    for product in page_obj:
        image_url = (
            product.images.first().image.url
            if product.images.exists()
            else "/static/images/default-product.png"
        )
        product_list.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description,
            "image": image_url,
        })
 
    context = {
        "store_name": store.name,
        "store_description": store.description,
        "products": page_obj,  # keep pagination context
        "product_list": product_list,  # list for rendering image URLs
        "categories": store_categories,
        "search_query": search_query,
        "selected_category": category_filter,
        "pagination_query": urlencode({"search": search_query, "category": category_filter}),
        "role": role,
        "user_store_id": user_store_id,
        "store_id": store.id,
    }
 
    return render(request, "storefront.html", context)


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

@csrf_exempt  
def add_or_edit_product(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        role = request.session.get('role')

        if role != 'merchant':
            return JsonResponse({'success': False, 'message': 'Unauthorized'})

        merchant = MerchantProfile.objects.filter(user_id=user_id).first()
        if not merchant or not merchant.store:
            return JsonResponse({'success': False, 'message': 'Merchant store not found'})

        store = merchant.store
        product_id = request.POST.get('product_id')
        is_delete = request.POST.get('delete') == 'true'
        is_undo = request.POST.get('undo') == 'true'

        # SOFT DELETE
        if is_delete:
            product = Product.objects.filter(id=product_id, store=store).first()
            if product:
                product.is_active = False
                product.save()
                return JsonResponse({'success': True, 'message': 'Product deleted (soft)'})
            return JsonResponse({'success': False, 'message': 'Product not found'})

        # UNDO DELETE
        if is_undo:
            product = Product.objects.filter(id=product_id, store=store).first()
            if product:
                product.is_active = True
                product.save()
                return JsonResponse({'success': True, 'message': 'Undo successful'})
            return JsonResponse({'success': False, 'message': 'Product not found'})

        # NORMAL ADD/EDIT
        name = request.POST.get('name')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description')
        images = request.FILES.getlist('images')
        category = store.category  # auto-fill category

        if not all([name, price, stock, description]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})

        if product_id:
            product = Product.objects.filter(id=product_id, store=store).first()
            if not product:
                return JsonResponse({'success': False, 'message': 'Product not found'})
            product.name = name
            product.price = price
            product.stock = stock
            product.description = description
            product.category = category
            product.save()
        else:
            product = Product.objects.create(
                store=store,
                name=name,
                price=price,
                stock=stock,
                description=description,
                category=category
            )

        if images:
            for img in images:
                ProductImage.objects.create(product=product, image=img)

        return JsonResponse({'success': True, 'message': 'Product saved'})

def admin_dashboard_view(request):
    # Replace this with your actual logic
    return render(request, 'admin_dashboard.html')

@login_required
@csrf_exempt
def get_merchant_products(request):
    user_id = request.session.get('user_id')
    role = request.session.get('role')

    if role != 'merchant':
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=403)

    merchant = MerchantProfile.objects.filter(user_id=user_id).first()
    if not merchant or not merchant.store:
        return JsonResponse({'success': False, 'message': 'Merchant store not found'}, status=404)

    products = Product.objects.filter(store=merchant.store, is_active=True).prefetch_related('images')

    data = []
    for product in products:
        images = [img.image.url for img in product.images.all()]
        data.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'stock': product.stock,
            'category': str(product.category),
            'description': product.description,
            'image': images[0] if images else '/static/images/default-product.png'
        })

    return JsonResponse({'success': True, 'products': data})




from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages


def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user, status='pending')

    if request.method == 'POST':
        order.status = 'confirmed'
        order.save()
        messages.success(request, "Your order has been confirmed!")
        return redirect('cart')  # or wherever you want to redirect
    

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Order, OrderItem

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Get or create an active order for the user
    order, created = Order.objects.get_or_create(user=request.user, status='pending')

    # Check if the product is already in the order
    order_item, item_created = OrderItem.objects.get_or_create(order=order, product=product)

    if not item_created:
        # If the item already exists, increment the quantity
        order_item.quantity += 1
        order_item.save()

    return redirect('cart_view')


@login_required
def cart_view(request):
    order = Order.objects.filter(user=request.user, status='pending').first()
    return render(request, 'cart.html', {'order': order})

@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    order = get_object_or_404(Order, user=request.user, status='pending')
    order_item = get_object_or_404(OrderItem, order=order, product=product)

    if order_item.quantity > 1:
        order_item.quantity -= 1
        order_item.save()
    else:
        order_item.delete()

    return redirect('cart_view')