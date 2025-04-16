import bcrypt
from collections import defaultdict
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import IntegrityError
from django.db.models import Prefetch
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.hashers import check_password
from django.utils.http import urlencode
from django.utils.text import slugify
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from .models import (
    CartItem,
    Category,
    Contact,
    CustomerProfile,
    MerchantProfile,
    Product,
    ProductImage,
    Store,
    Subscription,
    User
)




def generate_unique_slug(base_name):
    if not base_name or not isinstance(base_name, str):
        raise ValueError("Base name must be a non-empty string.")

    slug = slugify(base_name)
    unique_slug = slug
    num = 1
    while Store.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    return unique_slug


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

    if user.role != 'merchant':
        return redirect('home')

    profile = get_object_or_404(MerchantProfile.objects.select_related('store'), user=user)
    store = profile.store

    if not store:
        return render(request, 'dashboards/merchant_dashboard.html', {
            'profile': profile,
            'products': [],
            'categories': Category.objects.all(),
            'store_missing': True,
        })

    products = Product.objects.filter(store=store).prefetch_related('images')

    context = {
        'profile': profile,
        'store': store,
        'products': products,
        'categories': Category.objects.all(),
        'store_missing': False,
    }

    return render(request, 'dashboards/merchant_dashboard.html', context)


@login_required
def customer_dashboard(request):
    return HttpResponse("Welcome to the Customer Dashboard!")


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_superuser)(view_func)

@superuser_required
def internal_admin_dashboard(request):
    from .models import User, Store, Product, CartItem

    filter_target = request.GET.get("filter_target", "")
    query = request.GET.get("query", "")
    user_role = request.GET.get("user_role", "")
    store_status = request.GET.get("store_status", "")

    users = User.objects.all()
    stores = Store.objects.all()
    products = Product.objects.all()
    cart_items = CartItem.objects.all()

    if filter_target == "user" or filter_target == "":
        if query:
            users = users.filter(username__icontains=query)
        if user_role:
            users = users.filter(role=user_role)
    else:
        users = User.objects.none()

    if filter_target == "store" or filter_target == "":
        if query:
            stores = stores.filter(name__icontains=query)
        if store_status == "active":
            stores = stores.filter(is_store_active=True)
        elif store_status == "inactive":
            stores = stores.filter(is_store_active=False)
    else:
        stores = Store.objects.none()

    if filter_target == "product" or filter_target == "":
        if query:
            products = products.filter(name__icontains=query)
    else:
        products = Product.objects.none()

    if filter_target == "cart" or filter_target == "":
        if query:
            cart_items = cart_items.filter(product__name__icontains=query)
    else:
        cart_items = CartItem.objects.none()

    context = {
        'users': users,
        'stores': stores,
        'products': products,
        'cart_items': cart_items,
        'filter_target': filter_target,
        'query': query,
        'user_role': user_role,
        'store_status': store_status,
    }

    return render(request, 'dashboards/internal_admin_dashboard.html', context)


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
        "page_obj": page_obj
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
            slug = generate_unique_slug(store_name)

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
        'profile': profile,
        'store': profile.store
    })


def contact(request):
    return render(request, 'contact.html')

def auth_page(request):
    return render(request, 'auth.html')


def storefront_by_slug(request, slug):
    store = get_object_or_404(Store, slug=slug, is_store_active=True)
    
    # Get active products + related images
    products_qs = Product.objects.filter(store=store, is_active=True).prefetch_related("images")

    search_query = request.GET.get("search", "").strip().lower()
    category_filter = request.GET.get("category", "").strip()

    try:
        page_number = int(request.GET.get("page", 1))
    except ValueError:
        page_number = 1  # fallback to page 1 if invalid

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
        "products": page_obj,
        "product_list": product_list,
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
        username = request.POST.get('username', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        role = request.POST.get('role')
        email = request.POST.get('email', '').strip()
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

        if len(password1) < 6:
            return render(request, 'register.html', {'error': 'Password must be at least 6 characters long.'})

        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'register.html', {'error': 'Please enter a valid email address.'})

        if phone_number and (not phone_number.isdigit() or len(phone_number) < 8):
            return render(request, 'register.html', {'error': 'Enter a valid phone number.'})

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

        request.session['user_id'] = user.id
        request.session['username'] = user.username
        request.session['full_name'] = user.full_name
        request.session['role'] = user.role

        default_url = '/static/img/default-profile.png'
        profile_url = None

        if role == 'merchant':
            profile, _ = MerchantProfile.objects.get_or_create(user=user)
            if profile.profile_picture:
                profile_url = profile.profile_picture.url
            request.session['profile_picture_url'] = profile_url or default_url
            if not profile.is_profile_complete:
                return redirect('merchant_setup')
            return redirect('merchant_dashboard')

        elif role == 'customer':
            profile, _ = CustomerProfile.objects.get_or_create(user=user)
            if profile.profile_picture:
                profile_url = profile.profile_picture.url
            request.session['profile_picture_url'] = profile_url or default_url
            return redirect('explore')

        return redirect('login')

    return render(request, 'register.html')


@login_required
def merchant_dashboard(request):
    if request.user.role != 'merchant':
        messages.error(request, "Access denied.")
        return redirect('home')
    return render(request, 'dashboards/merchant_dashboard.html')

def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()  # Username or Email
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me') == 'on'

        if not identifier or not password:
            return render(request, 'login.html', {'error': 'Both username/email and password are required.'})

        user = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()

        if user and check_password(password, user.password):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            #  Set session values
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['full_name'] = user.full_name
            request.session['role'] = user.role

            default_url = '/static/img/default-profile.png'
            profile_url = None

            # superuser
            if user.is_superuser:
                request.session['profile_picture_url'] = profile_url or default_url
                return redirect('home')

            elif user.role == 'merchant':
                profile = MerchantProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url
                request.session['profile_picture_url'] = profile_url or default_url
                if not profile or not profile.is_profile_complete:
                    return redirect('merchant_setup')
                return redirect('merchant_dashboard')

            elif user.role == 'customer':
                profile = CustomerProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url
                request.session['profile_picture_url'] = profile_url or default_url
                return redirect('explore')

            return redirect('login')

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
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        description = request.POST.get('description', '').strip()
        images = request.FILES.getlist('images')
        category = store.category  # auto-fill category

        if not all([name, price, stock, description]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})

        if len(name) < 3:
            return JsonResponse({'success': False, 'message': 'Product name must be at least 3 characters.'})

        if len(description) < 10:
            return JsonResponse({'success': False, 'message': 'Description must be at least 10 characters.'})

        try:
            price = float(price)
            stock = int(stock)
            if price <= 0 or stock < 0:
                raise ValueError
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Price must be a positive number and stock must be a non-negative integer.'})

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

@staff_member_required
def admin_dashboard_view(request):
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


@login_required
def add_to_cart_dynamic(request):
    if request.method == 'POST':
        try:
            product_id = int(request.POST.get('product_id'))
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            messages.error(request, "Invalid product or quantity.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        product = get_object_or_404(Product, pk=product_id)

        if quantity <= 0 or quantity > product.stock:
            messages.error(request, "Invalid quantity selected.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        user = request.user

        if user.role == 'customer':
            customer = get_object_or_404(CustomerProfile, user=user)

            cart_item, created = CartItem.objects.get_or_create(
                customer=customer,
                product=product,
                defaults={'quantity': quantity}
            )

            if not created:
                cart_item.quantity += quantity
                if cart_item.quantity > product.stock:
                    cart_item.quantity = product.stock
                cart_item.save()

            product.stock -= quantity
            product.save()

            messages.success(request, f"{product.name} added to your cart.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        elif user.role == 'merchant':
            merchant = get_object_or_404(MerchantProfile, user=user)

            if merchant.store == product.store:
                messages.error(request, "You cannot order from your own store.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            messages.error(request, "Merchants are not allowed to place orders.")
            return redirect('home')

        else:
            messages.error(request, "Only customers can place orders.")
            return redirect('home')

@login_required
def create_customer_profile(request):
    user = request.user
    customer = CustomerProfile.objects.get(user=user)

    orders = customer.orders.all()
    order_stats = {
        'total': orders.count(),
        'pending': orders.filter(status='pending').count(),
        'cancelled': orders.filter(status='cancelled').count(),
        'delivered': orders.filter(status='delivered').count(),
    }

    recent_products = customer.recently_viewed.select_related('product')[:5]

    return render(request, 'customer_profile.html', {
        'customer': customer,
        'order_stats': order_stats,
        'recent_products': recent_products,
    })



@login_required
def edit_customer_profile(request):
    user = request.user
    customer = get_object_or_404(CustomerProfile, user=user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        profile_picture = request.FILES.get('profile_picture')

        # Validation
        if len(full_name) < 2:
            messages.error(request, "Full name must be at least 2 characters.")
            return redirect('edit_customer_profile')

        if not phone.isdigit() or len(phone) < 7:
            messages.error(request, "Enter a valid phone number.")
            return redirect('edit_customer_profile')

        if len(address) < 5:
            messages.error(request, "Address must be at least 5 characters.")
            return redirect('edit_customer_profile')

        # Update user fields
        user.full_name = full_name
        user.phone_number = phone
        user.save()

        # Update customer profile fields
        customer.address = address
        if profile_picture:
            customer.profile_picture = profile_picture
        customer.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('create_customer_profile')

    return render(request, 'edit_customer_profile.html', {
        'customer': customer,
    })

def customer_profile_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role == 'customer':
            if not CustomerProfile.objects.filter(user=request.user).exists():
                return redirect('create_customer_profile')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@customer_profile_required
def customer_dashboard(request):
    user = request.user

    if user.role != 'customer':
        return redirect('merchant_dashboard')

    customer_profile = CustomerProfile.objects.filter(user=user).first()
    if not customer_profile:
        return redirect('create_customer_profile')

    return render(request, 'dashboards/customer_dashboard.html', {
        'user': user,
        'customer_profile': customer_profile,
    })

    
@login_required
def view_cart(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    cart_items = customer.cart_items.select_related('product__store').prefetch_related('product__images')

    grouped_cart = defaultdict(lambda: {'items': [], 'total': 0})
    grand_total = 0

    for item in cart_items:
        if item.product and item.product.store:
            item.subtotal = item.quantity * item.product.price
            store = item.product.store
            grouped_cart[store]['items'].append(item)
            grouped_cart[store]['total'] += item.subtotal
            grand_total += item.subtotal

    return render(request, 'cart/view_cart.html', {
        'grouped_cart': dict(grouped_cart),
        'total': grand_total,
    })


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        if request.user.role != 'customer':
            return redirect('home')

        cart_item = get_object_or_404(CartItem, id=item_id, customer__user=request.user)
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0 or quantity > cart_item.product.stock:
            messages.error(request, "Invalid quantity.")
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Quantity updated.")

    return redirect('view_cart')


@login_required
def merchant_profile_page(request):
    if getattr(request.user, 'role', None) != 'merchant':
        messages.error(request, "Access denied. Only merchants can view this page.")
        return redirect('home')

    profile = get_object_or_404(MerchantProfile, user=request.user)
    store = profile.store

    store_link = None
    product_stats = {}

    if store:
        if store.slug:
            store_link = reverse('storefront_by_slug', kwargs={'slug': store.slug})

        products = store.product.all()
        product_stats = {
            'total': products.count(),
            'in_stock': sum(p.stock for p in products),
            'active': products.filter(is_active=True).count(),
            'inactive': products.filter(is_active=False).count(),
        }

    return render(request, 'merchant_profile.html', {
        'profile': profile,
        'store_link': store_link,
        'product_stats': product_stats,
    })

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

def contact_merchant(request):
    return

def download_cart_pdf(request):
    return


@login_required
def clear_cart(request):
    customer = get_object_or_404(CustomerProfile, user=request.user)
    customer.cart_items.all().delete()
    return redirect('view_cart')


@login_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, customer__user=request.user)

    try:
        qty_to_remove = int(request.POST.get('quantity'))
    except (TypeError, ValueError):
        qty_to_remove = item.quantity  # fallback to full removal

    if qty_to_remove <= 0:
        messages.error(request, "Invalid quantity.")
        return redirect('view_cart')

    if qty_to_remove >= item.quantity:
        item.product.stock += item.quantity
        item.product.save()
        item.delete()
        messages.success(request, "Item removed from cart.")
    else:
        item.quantity -= qty_to_remove
        item.product.stock += qty_to_remove
        item.product.save()
        item.save()
        messages.success(request, f"Removed {qty_to_remove} from cart item.")

    return redirect('view_cart')

def product_image_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    image = product.images.first()
    image_url = image.image.url if image else '/static/images/default-product.png'
    return JsonResponse({'image': image_url})


def contact(request):
    return render(request, 'contact.html')

    
@csrf_exempt  # Optional: remove if CSRF token is working correctly
def ajax_contact(request):
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    message = request.POST.get('message', '').strip()

    # Backend validation
    if len(name) < 2:
        return JsonResponse({'success': False, 'error': 'Name must be at least 2 characters.'})
    if '@' not in email or '.' not in email:
        return JsonResponse({'success': False, 'error': 'Please enter a valid email address.'})
    if len(message) < 10:
        return JsonResponse({'success': False, 'error': 'Message must be at least 10 characters.'})

    # Save to database
    contact_entry = Contact.objects.create(name=name, email=email, message=message)

    # Send email to admin
    try:
        send_mail(
            subject=f'New Contact Message from {name}',
            message=f'You received a new message from {name} <{email}>:\n\n{message}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['your_admin_email@example.com'],  # 🔁 Change this
            fail_silently=False,
        )
    except Exception as e:
        # Optional: log the error or send a fallback response
        return JsonResponse({'success': False, 'error': 'Message saved, but email failed to send.'})

    return JsonResponse({'success': True, 'message': 'Thank you for your message! We will get back to you shortly.'})


def edit_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.role = request.POST.get('role')
        user.save()
    return redirect('internal_admin_dashboard')


def edit_store_view(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    if request.method == 'POST':
        store.name = request.POST.get('name')
        store.description = request.POST.get('description')
        store.is_store_active = 'is_store_active' in request.POST
        store.save()
    return redirect('internal_admin_dashboard')


def edit_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.description = request.POST.get('description')
        product.save()
    return redirect('internal_admin_dashboard')


def edit_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        if quantity and quantity.isdigit():
            item.quantity = int(quantity)
            item.save()
    return redirect('internal_admin_dashboard')

def delete_user_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('internal_admin_dashboard')

def delete_store_view(request, store_id):
    store = get_object_or_404(Store, id=store_id)
    store.delete()
    return redirect('internal_admin_dashboard')

def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('internal_admin_dashboard')

def delete_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('internal_admin_dashboard')