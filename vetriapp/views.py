from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import *


def home(request):
    banners = Category.objects.all().order_by('-created_at') 
    return render(request, 'myapp/home.html', {'banners': banners})



#contact page

from django.http import HttpResponseBadRequest

def Contactus(request):
        if request.method == 'POST':
        # Extract form data from POST request
            name = request.POST.get('name')
            email = request.POST.get('email')
            mobile = request.POST.get('mobile')
            message = request.POST.get('message')

        # Basic validation for required fields
            if not name or not email or not mobile or not message:
                return HttpResponseBadRequest("All fields are required")

            # Save form data to the database
            contact_form = ContactForm.objects.create(
                name=name,
                email=email,
                mobile=mobile,
                message=message
            )

            # Send email to admin
            send_mail(
                'New Contact Form Submission',
                f'Name: {name}\nEmail: {email}\nMobile: {mobile}\nMessage: {message}',
                email,  # sender's email
                [settings.ADMIN_EMAIL], 
                fail_silently=False,
            )

            # Redirect or show success message
            return JsonResponse({'status': 'success', 'message': 'Thank you for contacting us. We will get back to you shortly.'})  
        return render(request, 'myapp/contactus.html')

#product list page
def product_list(request, category_id=None, brand_name=None):
    # categories = Category.objects.all()
    categories = Category.objects.all().order_by('created_at')  # Oldest categories first

    selected_category = None
    selected_brand = None
    products = Product.objects.all()  # Start with all products

    # If a category is selected, filter products by that category
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=selected_category)

    # Fetch only brands related to the selected category
    brands = products.values_list('brand', flat=True).distinct()

    # If a brand is selected, filter products by that brand
    if brand_name:
        selected_brand = brand_name.strip()
        # products = products.filter(brand__iexact=selected_brand)
        

    return render(request, 'myapp/products.html', {
        'products': products,
        'categories': categories,
        'brands': brands,  # Updated to show brands only within the selected category
        'selected_category': selected_category,
        'selected_brand': selected_brand
    })



from django.shortcuts import render, get_object_or_404
from .models import Product

def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:10]

    return render(request, "myapp/product_details.html", {
        "product": product,
        "related_products": related_products,
    })




from django.contrib import messages




from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings



def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            return render(request, 'myapp/register.html', {'error': 'Passwords do not match'})

        if User.objects.filter(username=username).exists():
            return render(request, 'myapp/register.html', {'error': 'Username already exists'})

        if User.objects.filter(email=email).exists():
            return render(request, 'myapp/register.html', {'error': 'Email already registered'})

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)

        # Log in the user immediately after registration
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)  # Logs the user in
            return redirect('/')  # Redirect to home page where the username will be displayed

        # Send Email to User
        subject_user = "Registration Successful"
        message_user = f"Hello {username},\n\nWelcome to our website! Your registration was successful."
        send_mail(subject_user, message_user, settings.EMAIL_HOST_USER, [email])

        # Send Email to Admin
        subject_admin = "New User Registered"
        message_admin = f"New user registered:\n\nUsername: {username}\nEmail: {email}"
        send_mail(subject_admin, message_admin, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL])

    return render(request, 'myapp/register.html')



def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')  # Redirect to home after login
        else:
            return render(request, 'myapp/login.html', {'error': 'Invalid credentials'})

    return render(request, 'myapp/login.html')

import random
otp_storage = {}

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            otp = random.randint(100000, 999999)
            otp_storage[email] = otp  
            request.session['reset_email'] = email  

            print(f"Generated OTP for {email}: {otp}")  # Debugging: Ensure OTP is generated

            try:
                send_mail(
                    "Password Reset OTP",
                    f"Your OTP for password reset is {otp}",
                    "your-email@gmail.com",
                    [email]
                )
                print(f"OTP sent successfully to {email}")  # Debugging: Ensure email is sent
                return JsonResponse({"status": "success"})
            except Exception as e:
                print(f"Email sending failed: {e}")  # Debugging: Check for email errors
                return JsonResponse({"status": "error", "error": "Failed to send OTP. Check email settings."})

        else:
            return JsonResponse({"status": "error", "error": "Email not found"})

    return render(request, 'myapp/forgot_password.html')



def verify_otp(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')  
        entered_otp = request.POST.get('otp', "").strip()  # Ensure it's not empty

        if not entered_otp:
            return JsonResponse({"status": "error", "error": "OTP cannot be empty"})

        if email in otp_storage:
            correct_otp = otp_storage[email]  # Retrieve correct OTP
            
            try:
                if str(correct_otp) == entered_otp:  
                    return JsonResponse({"status": "success"})
                else:
                    return JsonResponse({"status": "error", "error": "Invalid OTP"})
            except ValueError:
                return JsonResponse({"status": "error", "error": "Invalid OTP format"})

        return JsonResponse({"status": "error", "error": "OTP expired or email not found"})


def reset_password(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')  # Ensure correct session key
        if not email:
            return JsonResponse({"status": "error", "error": "Session expired. Please request OTP again."})

        new_password = request.POST.get('password')
        user = User.objects.filter(email=email).first()

        if user:
            user.set_password(new_password)
            user.save()

            # Clear session after password reset
            del request.session['reset_email']  

            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "error": "User not found"})




def user_logout(request):
    logout(request)
    return redirect('login')


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json

#     return JsonResponse({"success": False, "message": "Invalid request"})
@csrf_exempt
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "User not logged in"})

    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)

        # Check if there is enough stock
        if product.in_stock_qty < quantity:
            return JsonResponse({"success": False, "message": "Not enough stock available"})

        price = product.price if product.price is not None else product.original_price

        cart_item, created = Cart.objects.get_or_create(
            user=request.user, 
            product=product,
            defaults={
                "name": product.name,
                "quantity": quantity,
                "image": product.image,
                "price": price, 
                "original_price": product.original_price,
            }
        )

        if not created:
            if product.in_stock_qty >= (cart_item.quantity + quantity): 
                cart_item.quantity += quantity
                cart_item.save()
            else:
                return JsonResponse({"success": False, "message": "Not enough stock available"})

        # Get updated cart count (unique products only)
        cart_count = Cart.objects.filter(user=request.user).count()

        return JsonResponse({"success": True, "message": "Product added to cart!", "cart_count": cart_count})

    return JsonResponse({"success": False, "message": "Invalid request"})



from django.contrib.auth.decorators import login_required

def cart_page(request):
    if not request.user.is_authenticated:
        return render(request, "myapp/cart.html", {"cart_empty": True}) 
    cart_items = Cart.objects.filter(user=request.user)

    total_price = sum(
        (item.product.price if item.product.price is not None else item.product.price) * item.quantity
        for item in cart_items
    )
    return render(request, "myapp/cart.html", {"cart_items": cart_items, "total_price": total_price})

@csrf_exempt
def update_cart(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cart_id = data.get("cart_id")
        action = data.get("action")

        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)

        if action == "increase":
            if cart_item.quantity < cart_item.product.in_stock_qty:
                cart_item.quantity += 1
            else:
                return JsonResponse({"success": False, "message": "Not enough stock available"})
        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1

        cart_item.save()

        # Recalculate total price
        cart_items = Cart.objects.filter(user=request.user)
        total_price = sum(
            (item.product.price if item.product.price else item.product.original_price) * item.quantity
            for item in cart_items
        )

        return JsonResponse({"success": True, "quantity": cart_item.quantity, "total_price": total_price})

    return JsonResponse({"success": False})


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def remove_from_cart(request):
    if request.method == "POST":
        data = json.loads(request.body)
        cart_id = data.get("cart_id")

        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        cart_item.delete()

        cart_count = Cart.objects.filter(user=request.user).count()

        return JsonResponse({"success": True, "cart_count": cart_count})

    return JsonResponse({"success": False})





def Terms_conditions(request):
    return render(request, 'myapp/terms&condition.html')


def Privacy_policy(request):
    return render(request, 'myapp/privacypolicy.html')





def payment_page(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items:
        return redirect('cart')  

    total_price = sum(
        (item.product.price if item.product.price is not None else item.product.original_price) * item.quantity
        for item in cart_items
    )

    return render(request, "myapp/paymentpage.html", {"cart_items": cart_items, "total_price": total_price})

# from decimal import Decimal
# import uuid
# from django.db import transaction
# from django.shortcuts import render, redirect
# from django.http import HttpResponse, JsonResponse
# from django.urls import reverse_lazy
# from django.views.decorators.csrf import csrf_exempt
# from django.core.mail import send_mail
# from django.conf import settings
# import json
# import logging

# from .models import PaymentTransaction, BillingAddress, Cart, Order, OrderItem
# from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
# from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
# from phonepe.sdk.pg.env import Env

# # PhonePe API Configurations
# MERCHANT_ID = ""
# SALT_KEY = ""
# SALT_INDEX = 1
# ENV = Env.PROD
# UI_REDIRECT_URL = "http://127.0.0.1:8000/payment/payment_success/"


# phonepe_client = PhonePePaymentClient(
#     merchant_id=MERCHANT_ID,
#     salt_key=SALT_KEY,
#     salt_index=SALT_INDEX,
#     env=ENV,
# )

# logger = logging.getLogger(__name__)
# def generate_unique_order_id():
#     """Generate a truly unique order_id"""
#     while True:
#         order_id = str(uuid.uuid4())[:32]
#         if not PaymentTransaction.objects.filter(order_id=order_id).exists():
#             return order_id

# def process_payment(request):
#     if request.method == "POST" and request.user.is_authenticated:
#         try:
#             logger.info(f"Received POST data: {request.POST}")  # Debugging Log

#             with transaction.atomic():
#                 user = request.user

#                 # Capture billing details
#                 billing_data = {
#                     "user": user,
#                     "email": request.POST.get('email', '').strip(),
#                     "country": request.POST.get('country', '').strip(),
#                     "first_name": request.POST.get('first_name', '').strip(),
#                     "last_name": request.POST.get('last_name', '').strip(),
#                     "address": request.POST.get('address', '').strip(),
#                     "apartment": request.POST.get('apartment', '').strip(),
#                     "city": request.POST.get('city', '').strip(),
#                     "state": request.POST.get('state', '').strip(),
#                     "pincode": request.POST.get('pincode', '').strip(),
#                     "phone": request.POST.get('phone', '').strip(),
#                     "saved_info": request.POST.get('saved_info') == 'on',
#                 }

#                 logger.info(f"Billing Data: {billing_data}")  # Debugging Log

#                 billing_address = BillingAddress.objects.create(**billing_data)
#                 logger.info(f"Billing address saved: {billing_address.id}")  # Check if stored

#                 # Retrieve cart items
#                 cart_items = Cart.objects.filter(user=user)
#                 if not cart_items.exists():
#                     return HttpResponse("Your cart is empty.", status=400)

#                 total_cost = sum(item.product.price * item.quantity for item in cart_items)
#                 amount_in_paise = int(total_cost * 100)
#                 transaction_id = str(uuid.uuid4())[:32]

#                 # Ensure `order_id` is unique
#                 order_id = generate_unique_order_id()

#                 # Save payment transaction
#                 payment_transaction = PaymentTransaction.objects.create(
#                     user=user,
#                     transaction_id=transaction_id,
#                     order_id=order_id,
#                     status="INITIATED",
#                     amount=total_cost,
#                     billing_address=billing_address,
#                     email=billing_data["email"],
#                     country=billing_data["country"],
#                     first_name=billing_data["first_name"],
#                     last_name=billing_data["last_name"],
#                     address=billing_data["address"],
#                     apartment=billing_data["apartment"],
#                     city=billing_data["city"],
#                     state=billing_data["state"],
#                     pincode=billing_data["pincode"],
#                     phone=billing_data["phone"]
#                 )

#                 logger.info(f"Payment transaction saved: {payment_transaction.id}")

#                 # Initiate payment with PhonePe
#                 pay_page_request = PgPayRequest.pay_page_pay_request_builder(
#                     merchant_transaction_id=transaction_id,
#                     amount=amount_in_paise,
#                     redirect_mode="POST",
#                     redirect_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#                     callback_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#                 )

#                 pay_page_response = phonepe_client.pay(pay_page_request)
#                 pay_page_url = pay_page_response.data.instrument_response.redirect_info.url

#                 # Save the payment URL in the database
#                 payment_transaction.payment_url = pay_page_url
#                 payment_transaction.save()

#                 logger.info(f"Redirecting to: {pay_page_url}")

#                 return redirect(pay_page_url)

#         except Exception as e:
#             logger.error(f"Error during payment initiation: {e}")
#             return HttpResponse("An error occurred during payment initiation. Please try again.", status=500)

#     return HttpResponse("Invalid request method.", status=400)
from decimal import Decimal
import uuid
import logging
import json
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentTransaction, BillingAddress, Cart, Order, OrderItem

# PhonePe SDK imports
from phonepe.sdk.pg.env import Env
from phonepe.sdk.pg.payments.v1.payment_client import PhonePePaymentClient
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest

# PhonePe Credentials (live or test)
MERCHANT_ID = ""
SALT_KEY = ""
SALT_INDEX = 1
ENV = Env.PROD
UI_REDIRECT_URL = "http://127.0.0.1:8000/payment/payment_success/"

logger = logging.getLogger(__name__)

# Enable test mode if credentials are missing
IS_TEST_MODE = not MERCHANT_ID or not SALT_KEY

# Mock client class
class MockPhonePeClient:
    def pay(self, pay_request):
        class DummyResponse:
            class Data:
                class InstrumentResponse:
                    class RedirectInfo:
                        url = "/payment/success-simulated/"
                    redirect_info = RedirectInfo()
                instrument_response = InstrumentResponse()
            data = Data()
        return DummyResponse()

# Use real or mock client
phonepe_client = MockPhonePeClient() if IS_TEST_MODE else PhonePePaymentClient(
    merchant_id=MERCHANT_ID,
    salt_key=SALT_KEY,
    salt_index=SALT_INDEX,
    env=ENV,
)

# Generate unique order ID
def generate_unique_order_id():
    while True:
        order_id = str(uuid.uuid4())[:32]
        if not PaymentTransaction.objects.filter(order_id=order_id).exists():
            return order_id

# Payment view
# def process_payment(request):
#     if request.method == "POST" and request.user.is_authenticated:
#         try:
#             with transaction.atomic():
#                 user = request.user

#                 # Billing info
#                 billing_data = {
#                     "user": user,
#                     "email": request.POST.get('email', '').strip(),
#                     "country": request.POST.get('country', '').strip(),
#                     "first_name": request.POST.get('first_name', '').strip(),
#                     "last_name": request.POST.get('last_name', '').strip(),
#                     "address": request.POST.get('address', '').strip(),
#                     "apartment": request.POST.get('apartment', '').strip(),
#                     "city": request.POST.get('city', '').strip(),
#                     "state": request.POST.get('state', '').strip(),
#                     "pincode": request.POST.get('pincode', '').strip(),
#                     "phone": request.POST.get('phone', '').strip(),
#                     "saved_info": request.POST.get('saved_info') == 'on',
#                 }

#                 billing_address = BillingAddress.objects.create(**billing_data)

#                 # Cart & amount
#                 cart_items = Cart.objects.filter(user=user)
#                 if not cart_items.exists():
#                     return HttpResponse("Your cart is empty.", status=400)

#                 total_cost = sum(item.product.price * item.quantity for item in cart_items)
#                 amount_in_paise = int(total_cost * 100)
#                 transaction_id = str(uuid.uuid4())[:32]
#                 order_id = generate_unique_order_id()

#                 # Save transaction
#                 payment_transaction = PaymentTransaction.objects.create(
#                     user=user,
#                     transaction_id=transaction_id,
#                     order_id=order_id,
#                     status="INITIATED",
#                     amount=total_cost,
#                     billing_address=billing_address,
#                     email=billing_data["email"],
#                     country=billing_data["country"],
#                     first_name=billing_data["first_name"],
#                     last_name=billing_data["last_name"],
#                     address=billing_data["address"],
#                     apartment=billing_data["apartment"],
#                     city=billing_data["city"],
#                     state=billing_data["state"],
#                     pincode=billing_data["pincode"],
#                     phone=billing_data["phone"]
#                 )

#                 # Create pay request
#                 pay_page_request = PgPayRequest.pay_page_pay_request_builder(
#                     merchant_transaction_id=transaction_id,
#                     amount=amount_in_paise,
#                     redirect_mode="POST",
#                     redirect_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#                     callback_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#                 )

#                 pay_page_response = phonepe_client.pay(pay_page_request)
#                 pay_page_url = (
#                     request.build_absolute_uri(reverse_lazy('payment_success_simulated'))
#                     if IS_TEST_MODE else pay_page_response.data.instrument_response.redirect_info.url
#                 )

#                 payment_transaction.payment_url = pay_page_url
#                 payment_transaction.save()

#                 return redirect(pay_page_url)

#         except Exception as e:
#             logger.error(f"Error during payment initiation: {e}")
#             return HttpResponse("An error occurred during payment initiation.", status=500)

#     return HttpResponse("Invalid request method.", status=400)
# from django.contrib.auth.decorators import login_required

# @login_required(login_url='/login/')
# def process_payment(request):
#     if request.method != "POST":
#         return HttpResponse("Invalid request method.", status=400)

#     try:
#         with transaction.atomic():
#             user = request.user

#             billing_data = {
#                 "user": user,
#                 "email": request.POST.get('email', '').strip(),
#                 "country": request.POST.get('country', '').strip(),
#                 "first_name": request.POST.get('first_name', '').strip(),
#                 "last_name": request.POST.get('last_name', '').strip(),
#                 "address": request.POST.get('address', '').strip(),
#                 "apartment": request.POST.get('apartment', '').strip(),
#                 "city": request.POST.get('city', '').strip(),
#                 "state": request.POST.get('state', '').strip(),
#                 "pincode": request.POST.get('pincode', '').strip(),
#                 "phone": request.POST.get('phone', '').strip(),
#                 "saved_info": request.POST.get('saved_info') == 'on',
#             }

#             billing_address = BillingAddress.objects.create(**billing_data)

#             cart_items = Cart.objects.filter(user=user)
#             if not cart_items.exists():
#                 return HttpResponse("Your cart is empty.", status=400)

#             total_cost = sum(
#                 (item.product.price if item.product.price is not None else item.product.original_price) * item.quantity
#                 for item in cart_items
#             )

#             if total_cost <= 0:
#                 return HttpResponse("Invalid amount.", status=400)

#             amount_in_paise = int(Decimal(total_cost) * 100)
#             transaction_id = str(uuid.uuid4())[:32]
#             order_id = generate_unique_order_id()

#             payment_transaction = PaymentTransaction.objects.create(
#                 user=user,
#                 transaction_id=transaction_id,
#                 order_id=order_id,
#                 status="INITIATED",
#                 amount=total_cost,
#                 billing_address=billing_address,
#                 email=billing_data["email"],
#                 country=billing_data["country"],
#                 first_name=billing_data["first_name"],
#                 last_name=billing_data["last_name"],
#                 address=billing_data["address"],
#                 apartment=billing_data["apartment"],
#                 city=billing_data["city"],
#                 state=billing_data["state"],
#                 pincode=billing_data["pincode"],
#                 phone=billing_data["phone"]
#             )

#             pay_page_request = PgPayRequest.pay_page_pay_request_builder(
#                 merchant_transaction_id=transaction_id,
#                 amount=amount_in_paise,
#                 redirect_mode="POST",
#                 redirect_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#                 callback_url=request.build_absolute_uri(reverse_lazy('payment_callback')),
#             )

#             pay_page_response = phonepe_client.pay(pay_page_request)

#             if IS_TEST_MODE:
#                 pay_page_url = request.build_absolute_uri(reverse_lazy('payment_success_simulated'))
#             else:
#                 pay_page_url = pay_page_response.data.instrument_response.redirect_info.url

#             payment_transaction.payment_url = pay_page_url
#             payment_transaction.save()

#             return redirect(pay_page_url)

#     except Exception as e:
#         logger.exception("Error during payment initiation")
#         return HttpResponse(f"Payment init error: {e}", status=500)
# import razorpay
# from decimal import Decimal
# import uuid
# from django.conf import settings
# from django.http import JsonResponse, HttpResponse
# from django.db import transaction
# from django.contrib.auth.decorators import login_required

# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# @login_required(login_url='/login/')
# def process_payment(request):
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

#     user = request.user
#     cart_items = Cart.objects.filter(user=user)
#     if not cart_items.exists():
#         return JsonResponse({"success": False, "message": "Cart empty"}, status=400)

#     total_cost = sum(
#         (item.product.price if item.product.price is not None else item.product.original_price) * item.quantity
#         for item in cart_items
#     )
#     amount_paise = int(Decimal(total_cost) * 100)

#     with transaction.atomic():
#         billing_address = BillingAddress.objects.create(
#             user=user,
#             email=request.POST.get('email','').strip(),
#             country=request.POST.get('country','').strip(),
#             first_name=request.POST.get('first_name','').strip(),
#             last_name=request.POST.get('last_name','').strip(),
#             address=request.POST.get('address','').strip(),
#             apartment=request.POST.get('apartment','').strip(),
#             city=request.POST.get('city','').strip(),
#             state=request.POST.get('state','').strip(),
#             pincode=request.POST.get('pincode','').strip(),
#             phone=request.POST.get('phone','').strip(),
#             saved_info=request.POST.get('saved_info') == 'on',
#         )

#         rp_order = razorpay_client.order.create({
#             "amount": amount_paise,
#             "currency": "INR",
#             "payment_capture": 1
#         })

#         PaymentTransaction.objects.create(
#             user=user,
#             transaction_id=str(uuid.uuid4())[:32],
#             order_id=rp_order["id"],   # Razorpay order_id stored here
#             status="INITIATED",
#             amount=Decimal(total_cost),
#             billing_address=billing_address,
#             email=billing_address.email,
#             country=billing_address.country,
#             first_name=billing_address.first_name,
#             last_name=billing_address.last_name,
#             address=billing_address.address,
#             apartment=billing_address.apartment,
#             city=billing_address.city,
#             state=billing_address.state,
#             pincode=billing_address.pincode,
#             phone=billing_address.phone
#         )

#     return JsonResponse({
#         "success": True,
#         "key": settings.RAZORPAY_KEY_ID,
#         "amount": amount_paise,
#         "razorpay_order_id": rp_order["id"],
#         "currency": "INR"
#     })
# from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import redirect

# @csrf_exempt
# @login_required(login_url='/login/')
# def razorpay_verify_payment(request):
#     if request.method != "POST":
#         return HttpResponse("Invalid request", status=400)

#     user = request.user
#     razorpay_order_id = request.POST.get("razorpay_order_id")
#     razorpay_payment_id = request.POST.get("razorpay_payment_id")
#     razorpay_signature = request.POST.get("razorpay_signature")

#     try:
#         razorpay_client.utility.verify_payment_signature({
#             "razorpay_order_id": razorpay_order_id,
#             "razorpay_payment_id": razorpay_payment_id,
#             "razorpay_signature": razorpay_signature
#         })
#     except:
#         return HttpResponse("Payment verification failed", status=400)

#     with transaction.atomic():
#         payment_txn = PaymentTransaction.objects.filter(user=user, order_id=razorpay_order_id).last()
#         if not payment_txn:
#             return HttpResponse("Transaction not found", status=400)

#         payment_txn.status = "SUCCESS"
#         payment_txn.save()

#         cart_items = Cart.objects.filter(user=user)
#         order = Order.objects.filter(transaction=payment_txn).first()

#         if not order:
#             order = Order.objects.create(
#                 user=user,
#                 transaction=payment_txn,
#                 price=payment_txn.amount,
#                 billing_address=payment_txn.billing_address
#             )

#             for item in cart_items:
#                 product = item.product
#                 if product.in_stock_qty < item.quantity:
#                     return HttpResponse(f"Insufficient stock for {product.name}", status=400)

#                 product.in_stock_qty -= item.quantity
#                 product.save()

#                 OrderItem.objects.create(
#                     order=order,
#                     product=product,
#                     quantity=item.quantity,
#                     price=(product.price if product.price is not None else product.original_price)
#                 )

#         cart_items.delete()
#         send_invoice_email(order.id)

#     return redirect("payment_success")

import uuid
import json
import hmac
import base64
import hashlib
import requests

from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import PaymentTransaction, BillingAddress, Cart, Order, OrderItem


def _cashfree_base_url():
    if settings.CASHFREE_ENV.upper() == "PRODUCTION":
        return "https://api.cashfree.com/pg"
    return "https://sandbox.cashfree.com/pg"


def _cashfree_headers():
    return {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-version": "2023-08-01",
        "x-client-id": settings.CASHFREE_APP_ID,
        "x-client-secret": settings.CASHFREE_SECRET_KEY,
    }


@login_required(login_url='/login/')
def process_payment(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        return JsonResponse({"success": False, "message": "Cart is empty"}, status=400)

    total_cost = sum(
        (item.product.price if item.product.price is not None else item.product.original_price) * item.quantity
        for item in cart_items
    )

    if Decimal(total_cost) <= 0:
        return JsonResponse({"success": False, "message": "Invalid amount"}, status=400)

    with transaction.atomic():
        billing_address = BillingAddress.objects.create(
            user=user,
            email=request.POST.get("email", "").strip(),
            country=request.POST.get("country", "").strip(),
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            address=request.POST.get("address", "").strip(),
            apartment=request.POST.get("apartment", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            pincode=request.POST.get("pincode", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            saved_info=request.POST.get("saved_info") == "on",
        )

        order_id = f"order_{uuid.uuid4().hex[:20]}"
        amount_value = float(Decimal(total_cost))

        payload = {
            "order_id": order_id,
            "order_amount": amount_value,
            "order_currency": "INR",
            "customer_details": {
                "customer_id": str(user.id),
                "customer_name": f"{billing_address.first_name} {billing_address.last_name}".strip() or user.username,
                "customer_email": billing_address.email or user.email,
                "customer_phone": billing_address.phone or "9999999999",
            },
            "order_meta": {
                "return_url": request.build_absolute_uri(f"/payment/cashfree/return/?order_id={order_id}"),
                "notify_url": request.build_absolute_uri("/payment/cashfree/webhook/"),
            },
            "order_note": f"Order for user {user.username}",
        }

        response = requests.post(
            f"{_cashfree_base_url()}/orders",
            headers=_cashfree_headers(),
            json=payload,
            timeout=30,
        )

        if response.status_code not in [200, 201]:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Cashfree order creation failed",
                    "details": response.text,
                },
                status=400,
            )

        cf_data = response.json()

        PaymentTransaction.objects.create(
            user=user,
            transaction_id=str(uuid.uuid4())[:32],
            order_id=order_id,
            status="INITIATED",
            amount=Decimal(str(total_cost)),
            billing_address=billing_address,
            email=billing_address.email,
            country=billing_address.country,
            first_name=billing_address.first_name,
            last_name=billing_address.last_name,
            address=billing_address.address,
            apartment=billing_address.apartment,
            city=billing_address.city,
            state=billing_address.state,
            pincode=billing_address.pincode,
            phone=billing_address.phone,
        )

    return JsonResponse({
        "success": True,
        "payment_session_id": cf_data.get("payment_session_id"),
        "order_id": order_id,
        "order_amount": amount_value,
        "customer_name": payload["customer_details"]["customer_name"],
        "customer_email": payload["customer_details"]["customer_email"],
        "customer_phone": payload["customer_details"]["customer_phone"],
    })


@login_required(login_url='/login/')
def cashfree_return(request):
    order_id = request.GET.get("order_id")

    if not order_id:
        return HttpResponse("Order ID missing", status=400)

    payment_txn = PaymentTransaction.objects.filter(order_id=order_id, user=request.user).last()
    if not payment_txn:
        return HttpResponse("Transaction not found", status=404)

    try:
        response = requests.get(
            f"{_cashfree_base_url()}/orders/{order_id}/payments",
            headers=_cashfree_headers(),
            timeout=30,
        )

        if response.status_code != 200:
            return HttpResponse("Unable to verify payment", status=400)

        payments = response.json()

        # Find SUCCESS payment
        success_payment = None
        for p in payments:
            if p.get("payment_status") == "SUCCESS":
                success_payment = p
                break

        if success_payment:
            with transaction.atomic():

                if payment_txn.status != "SUCCESS":
                    payment_txn.status = "SUCCESS"
                    payment_txn.save()

                # Order create
                order_obj = Order.objects.filter(transaction=payment_txn).first()

                if not order_obj:
                    cart_items = Cart.objects.filter(user=request.user)

                    order_obj = Order.objects.create(
                        user=request.user,
                        transaction=payment_txn,
                        price=payment_txn.amount,
                        billing_address=payment_txn.billing_address
                    )

                    for item in cart_items:
                        product = item.product

                        if product.in_stock_qty < item.quantity:
                            return HttpResponse(f"Stock issue: {product.name}", status=400)

                        product.in_stock_qty -= item.quantity
                        product.save()

                        OrderItem.objects.create(
                            order=order_obj,
                            product=product,
                            quantity=item.quantity,
                            price=(product.price if product.price else product.original_price)
                        )

                    cart_items.delete()
                    send_invoice_email(order_obj.id)

            return redirect("payment_success")

        else:
            return redirect("cartpage")

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

def _verify_cashfree_signature(request):
    """
    Verify webhook signature using raw body.
    """
    raw_body = request.body
    timestamp = request.headers.get("x-webhook-timestamp", "")
    received_signature = request.headers.get("x-webhook-signature", "")

    signed_payload = timestamp.encode("utf-8") + raw_body
    digest = hmac.new(
        settings.CASHFREE_SECRET_KEY.encode("utf-8"),
        signed_payload,
        hashlib.sha256
    ).digest()
    generated_signature = base64.b64encode(digest).decode("utf-8")

    return hmac.compare_digest(generated_signature, received_signature)


@csrf_exempt
def cashfree_webhook(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)

    if not _verify_cashfree_signature(request):
        return HttpResponse("Invalid signature", status=400)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponse("Invalid JSON", status=400)

    data = payload.get("data", {})
    order = data.get("order", {})
    payment = data.get("payment", {})

    cf_order_id = order.get("order_id")
    payment_status = payment.get("payment_status")

    if not cf_order_id:
        return HttpResponse("Missing order_id", status=400)

    payment_txn = PaymentTransaction.objects.filter(order_id=cf_order_id).last()
    if not payment_txn:
        return HttpResponse("Transaction not found", status=404)

    # Only mark success for successful webhook event
    if payment_status == "SUCCESS":
        with transaction.atomic():
            if payment_txn.status != "SUCCESS":
                payment_txn.status = "SUCCESS"
                payment_txn.save()

            existing_order = Order.objects.filter(transaction=payment_txn).first()
            if existing_order:
                return HttpResponse("OK", status=200)

            cart_items = Cart.objects.filter(user=payment_txn.user)
            if not cart_items.exists():
                return HttpResponse("OK", status=200)

            order_obj = Order.objects.create(
                user=payment_txn.user,
                transaction=payment_txn,
                price=payment_txn.amount,
                billing_address=payment_txn.billing_address
            )

            for item in cart_items:
                product = item.product
                if product.in_stock_qty < item.quantity:
                    return HttpResponse(f"Insufficient stock for {product.name}", status=400)

                product.in_stock_qty -= item.quantity
                product.save()

                OrderItem.objects.create(
                    order=order_obj,
                    product=product,
                    quantity=item.quantity,
                    price=(product.price if product.price is not None else product.original_price)
                )

            cart_items.delete()
            send_invoice_email(order_obj.id)

    elif payment_status in ["FAILED", "CANCELLED", "USER_DROPPED"]:
        payment_txn.status = payment_status
        payment_txn.save()

    return HttpResponse("OK", status=200)


@login_required(login_url='/login/')
def payment_status_check(request):
    """
    Frontend polls this after browser returns from Cashfree.
    """
    order_id = request.GET.get("order_id")
    tx = PaymentTransaction.objects.filter(order_id=order_id, user=request.user).last()

    if not tx:
        return JsonResponse({"success": False, "status": "NOT_FOUND"}, status=404)

    if tx.status == "SUCCESS":
        order_obj = Order.objects.filter(transaction=tx).first()
        return JsonResponse({
            "success": True,
            "status": "SUCCESS",
            "redirect_url": "/payment-success/" if not order_obj else f"/payment-success/?order_id={order_obj.id}"
        })

    return JsonResponse({
        "success": True,
        "status": tx.status
    })
# def payment_success_simulated(request):
#     user = request.user
#     if user.is_authenticated:
#         # Clear cart
#         Cart.objects.filter(user=user).delete()
#         # Mark transaction success
#         PaymentTransaction.objects.filter(user=user).last().status = "SUCCESS"

#         # Show confirmation and redirect to cart
#         html = """
#         <html>
#         <head>
#             <meta http-equiv="refresh" content="2;url=/cartpage/" />
#             <style>
#                 body { font-family: Arial; text-align: center; padding-top: 50px; }
#                 .message {
#                     font-size: 22px;
#                     color: green;
#                 }
#             </style>
#         </head>
#         <body>
#             <div class="message">✅ Payment Simulated Successfully!<br>Redirecting to your cart...</div>
#         </body>
#         </html>
#         """
#         return HttpResponse(html)
#     return HttpResponse("Login required.", status=403)
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction

@login_required
def payment_success_simulated(request):
    user = request.user

    with transaction.atomic():
        # 1) cart எடுத்துக்கோ
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return redirect("/cartpage/")

        # 2) last transaction எடுத்துக்கோ
        payment_txn = PaymentTransaction.objects.filter(user=user).last()
        if not payment_txn:
            return HttpResponse("No transaction found", status=400)

        # 3) status update + save
        payment_txn.status = "SUCCESS"
        payment_txn.save()

        # 4) Order create (duplicate avoid)
        order = Order.objects.filter(transaction=payment_txn).first()
        if not order:
            order = Order.objects.create(
                user=user,
                transaction=payment_txn,
                price=payment_txn.amount,
                billing_address=payment_txn.billing_address,
            )

            # 5) OrderItems create + stock reduce
            for item in cart_items:
                product = item.product
                if product.in_stock_qty < item.quantity:
                    return HttpResponse(f"Insufficient stock for {product.name}", status=400)

                product.in_stock_qty -= item.quantity
                product.save()

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=(product.price if product.price is not None else product.original_price),
                )

        # 6) cart clear
        cart_items.delete()

        # 7) Send invoice email
        send_invoice_email(order.id)

    # ✅ redirect to success page (shows order)
    return redirect("payment_success")
 # or redirect(f"/payment/order-success/{order.id}/")


import json
import logging
from decimal import Decimal
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@csrf_exempt
def payment_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == "application/json" else request.POST

            transaction_id = data.get('transactionId')
            status = data.get('code')
            amount = Decimal(data.get('amount')) / 100

            if not transaction_id or not status or not amount:
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

            payment_transaction, created = PaymentTransaction.objects.get_or_create(transaction_id=transaction_id)

            # Update transaction status
            payment_transaction.status = status
            payment_transaction.amount = amount
            payment_transaction.save()

            order = None  # Ensure order is always initialized

            if status == "PAYMENT_SUCCESS":
                # Ensure we don't create a duplicate order
                if not Order.objects.filter(transaction=payment_transaction).exists():
                    with transaction.atomic():
                        billing_address = payment_transaction.billing_address
                        order = Order.objects.create(
                            user=payment_transaction.user,
                            transaction=payment_transaction,
                            price=payment_transaction.amount,  # Updated field name
                            billing_address=billing_address,
                        )

                        # Move cart items to OrderItems
                        cart_items = Cart.objects.filter(user=payment_transaction.user)
                        for cart_item in cart_items:
                            product = cart_item.product
                            quantity = cart_item.quantity

                            if product.in_stock_qty >= quantity:
                                product.in_stock_qty -= quantity
                                product.save()

                                OrderItem.objects.create(
                                    order=order,
                                    product=cart_item.product,
                                    quantity=cart_item.quantity,
                                    price=cart_item.product.price,
                                )

                            else:
                                return JsonResponse({'status': 'error', 'message': 'Insufficient stock'}, status=400)

                        # Clear the cart after successful order
                        cart_items.delete()

                        send_invoice_email(order.id)

                return render(request, 'myapp/payment_success.html', {'order': order})

            return JsonResponse({'status': 'error', 'message': 'Payment failed'}, status=400)

        except Exception as e:
            logger.error(f"Error in callback: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': 'Internal server error'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def Order_success(request):
    order = Order.objects.last() 

    return render(request, 'myapp/payment_success.html', {'order': order})



from django.shortcuts import render, get_object_or_404

def product_list(request, category_id=None, brand_name=None):
    categories = Category.objects.all()  # Fetch all categories
    selected_category = None
    selected_brand = None
    products = Product.objects.all()  # Start with all products

    # Filter by category
    if category_id:
        selected_category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=selected_category)

    # Fetch only brands related to the selected category
    brands = products.values_list('brand', flat=True).distinct()

    # Filter by brand (if provided)
    if brand_name:
        selected_brand = brand_name.strip()
        products = products.filter(brand__iexact=selected_brand)

    return render(request, 'myapp/products.html', {
        'products': products,
        'categories': categories,
        'brands': brands, 
        'selected_category': selected_category,
        'selected_brand': selected_brand
    })

@login_required(login_url='/login/')
def Our_orders(request):   
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/our_orders.html', {'orders': orders})


from django.db.models import Q

def live_search(request):
    """ Returns search results as JSON for live search. """
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(brand__icontains=query) | 
            Q(description__icontains=query)
        )[:5]  # Limit results to 5
    
        results = [{'id': p.id, 'name': p.name, 'image': p.image.url} for p in products]
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

def search_results(request):
    """ Render full search results page """
    query = request.GET.get('q', '')
    
    products = Product.objects.filter(
        Q(name__icontains=query) | 
        Q(brand__icontains=query) | 
        Q(description__icontains=query)
    )

    return render(request, 'myapp/search.html', {'products': products, 'query': query})



def track_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()  # Fetch all items related to this order
    
    status_steps = ["Order Confirmed", "Processing", "Shipped", "Delivered"]

    return render(request, 'myapp/track_order.html', {
        'order': order,
        'order_items': order_items,
        'status_steps': status_steps
    })



from django.template.loader import render_to_string
from weasyprint import HTML
import os
from datetime import datetime
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem

def generate_invoice_pdf(order_id):
    # Fetch the order instance
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)

    # Extract customer details
    customer_name = f"{order.transaction.first_name} {order.transaction.last_name}" if order.transaction.first_name else "N/A"
    customer_email = order.transaction.email if order.transaction.email else "N/A"
    customer_phone = order.transaction.phone if order.transaction.phone else "N/A"
    customer_address = (
        f"{order.transaction.address}, {order.transaction.city}, {order.transaction.state} - {order.transaction.pincode}"
        if order.transaction.address else "N/A"
    )

    # Prepare context for rendering invoice template
    context = {
        'order': order,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'customer_address': customer_address,
        'order_items': order_items,
    }

    # Render HTML template to string
    html_string = render_to_string('myapp/invoice.html', context)

    # Create a unique filename with timestamp
    pdf_directory = os.path.join(os.getcwd(), 'order_invoices')
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    pdf_file_path = os.path.join(pdf_directory, f'invoice_{order_id}_{timestamp}.pdf')

    # Generate PDF
    HTML(string=html_string).write_pdf(pdf_file_path)

    return pdf_file_path if os.path.exists(pdf_file_path) else None


from django.http import FileResponse, Http404

def download_invoice(request, order_id):
    # Fetch the order
    order = get_object_or_404(Order, id=order_id)

    # Always generate a fresh invoice before downloading
    pdf_file_path = generate_invoice_pdf(order_id)

    if not pdf_file_path or not os.path.exists(pdf_file_path):
        raise Http404("Invoice file not found.")

    response = FileResponse(open(pdf_file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
    return response

from django.core.mail import EmailMessage
from django.conf import settings

def send_invoice_email(order_id):
    try:
        # Generate invoice PDF
        pdf_file_path = generate_invoice_pdf(order_id)

        if not pdf_file_path:
            print(f"Invoice generation failed for order {order_id}.")
            return

        # Fetch order details
        order = Order.objects.get(id=order_id)
        user_email = order.user.email
        admin_email = settings.ADMIN_EMAIL  # Ensure this is set in settings.py

        # Fetch ordered items
        ordered_items = order.items.all() 
        
        # Prepare order details
        order_details = "\n".join([
            f"{item.product.name} - Qty: {item.quantity}, Price: ₹{item.price}"
            for item in ordered_items
        ])

        total_price = sum(item.price * item.quantity for item in ordered_items)

        # Email content for user mail
        user_subject = f"Thank You for Your Order #{order.id}"

        user_message = (
            f"Dear {order.user.username},\n\n"
            "Thank you for your order!\n\n"
            "=========================================\n"
            "              ORDER DETAILS              \n"
            "=========================================\n"
            "Item Name - Quantity & Price  \n"
            "-----------------------------------------\n"
            f"{order_details}\n"  
            "-----------------------------------------\n"
            f"Total Amount: ₹{total_price}\n\n"
            "Please find the attached invoice.\n\n"
            "Best Regards,\nVetri Electronics"
        )


        # Email content for admin mail
        admin_subject = f"New Order Received: Order #{order.id}"
        admin_message = (
            f"Hello Admin,\n\n"
            "=========================================\n"
            "            NEW ORDER DETAILS           \n"
            "=========================================\n"
            f"Order ID: {order.id}\n"
            f"Customer: {order.user.username}\n"
            f"Email: {user_email}\n\n"
            "=========================================\n"
            "              ORDER ITEMS                \n"
            "=========================================\n"
            "Item Name & Quantity & Price  \n"
            "-----------------------------------------\n"
            f"{order_details}\n"  
            "-----------------------------------------\n"
            f"Total Amount: ₹{total_price}\n\n"
            "Invoice attached.\n\n"
            "Best Regards,\nVetri Electronics"
        )

        # Send user email
        user_email_msg = EmailMessage(
            subject=user_subject,
            body=user_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )

        # Send admin email
        admin_email_msg = EmailMessage(
            subject=admin_subject,
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )

        # Attach PDF invoice to both emails
        with open(pdf_file_path, 'rb') as pdf_file:
            user_email_msg.attach(f'invoice_{order_id}.pdf', pdf_file.read(), 'application/pdf')

        with open(pdf_file_path, 'rb') as pdf_file:
            admin_email_msg.attach(f'invoice_{order_id}.pdf', pdf_file.read(), 'application/pdf')

        # Send emails
        user_email_msg.send()
        admin_email_msg.send()

        print(f"Invoice email sent successfully to {user_email} and {admin_email}")

    except Exception as e:
        print(f"Failed to send invoice email: {e}")


from django.shortcuts import render, get_object_or_404

def Invoice(request, order_id):
    # Fetch the specific order
    order = get_object_or_404(Order, id=order_id)

    # Fetch all items related to the order
    order_items = OrderItem.objects.filter(order=order)

    # Extract customer details
    transaction = order.transaction
    customer_name = f"{transaction.first_name} {transaction.last_name}" if transaction.first_name else "N/A"
    customer_email = transaction.email if transaction.email else "N/A"
    customer_phone = transaction.phone if transaction.phone else "N/A"
    customer_address = (
        f"{transaction.address}, {transaction.city}, {transaction.state} - {transaction.pincode}"
        if transaction.address else "N/A"
    )

    context = {
        'order': order,
        'order_items': order_items,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_phone': customer_phone,
        'customer_address': customer_address,
    }

    return render(request, 'myapp/invoice.html', context)


