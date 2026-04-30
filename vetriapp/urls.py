from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # =========================
    # HOME & BASIC
    # =========================
    path('', views.home, name='home'),
    path('contactus', views.Contactus, name='contactus'),

    # =========================
    # PRODUCTS
    # =========================
    path('products', views.product_list, name='products'),
    path('products/category/<int:category_id>/', views.product_list, name='products_by_category'), 
    path('products/category/<int:category_id>/brand/<str:brand_name>/', views.product_list, name='products_by_brand'),
    path('product/<int:product_id>/', views.product_details, name='product_details'),

    # =========================
    # AUTH
    # =========================
    path('login/', views.user_login, name='login'),  
    path('register/', views.register, name='register'), 
    path('logout/', views.user_logout, name='logout'),

    # =========================
    # PASSWORD RESET
    # =========================
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("reset-password/", views.reset_password, name="reset_password"), 

    # =========================
    # CART
    # =========================
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cartpage/', views.cart_page, name='cartpage'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),

    # =========================
    # STATIC PAGES
    # =========================
    path('termscondition', views.Terms_conditions, name='termscondition'),
    path('privacypolicy', views.Privacy_policy, name='privacypolicy'),

    # =========================
    # PAYMENT (CASHFREE)
    # =========================
    path('checkout/payment/', views.payment_page, name='payment_page'),
    path("payment/process/", views.process_payment, name="process_payment"),
    path("payment/cashfree/return/", views.cashfree_return, name="cashfree_return"),
    path("payment/cashfree/webhook/", views.cashfree_webhook, name="cashfree_webhook"),
    path("payment/status-check/", views.payment_status_check, name="payment_status_check"),

    # =========================
    # ORDER & INVOICE
    # =========================
    path('payment/success/', views.Order_success, name='payment_success'),
    path('invoice', views.Invoice, name='invoice'),
    path('invoice/<int:order_id>/', views.Invoice, name='invoice_detail'),
    path('order/<int:order_id>/download-invoice/', views.download_invoice, name='download_invoice'),

    # =========================
    # ORDERS & SEARCH
    # =========================
    path('ourorders/', views.Our_orders, name='ourorders'),
    path('products/search/', views.search_results, name='search_results'),
    path('products/live_search/', views.live_search, name='live_search'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
]

# MEDIA FILES
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)