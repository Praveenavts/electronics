from django.db import models


class Category(models.Model):
    category = models.ImageField(upload_to="category/", null=True)
    banner = models.ImageField(upload_to="banner/", null=True)
    
    category_name = models.CharField(max_length=150, null=True)
    description = models.TextField(
        help_text="Enter one description per line with icons (e.g. 📱, 📶, ⚡...)"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.category_name

    class Meta:
        ordering = ['created_at']  


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE) 
    name = models.CharField(max_length=255, null=True) 
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=255, null=True)
    image = models.ImageField(upload_to="products/", null=True)  
    original_price = models.DecimalField(max_digits=10, decimal_places=2)  
    price = models.DecimalField(max_digits=10, decimal_places=2)  
    in_stock_qty = models.DecimalField(max_digits=3,decimal_places=0, null=True)
    in_stock = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        """ Automatically update 'in_stock' based on available stock quantity """
        self.in_stock = self.in_stock_qty > 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    

from django.contrib.auth.models import User

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True)
    quantity = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to="products/", null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True) 

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.quantity})"


    

from django.db import models
from django.contrib.auth.models import User

class BillingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    country = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    address = models.TextField()
    apartment = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    saved_info = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.address}"
    
from django.utils import timezone

class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100, unique=True)
    transaction_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, default="INITIATED")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    billing_address = models.ForeignKey(BillingAddress, on_delete=models.CASCADE)
    payment_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)    
    email = models.EmailField(null=True)
    country = models.CharField(max_length=100, null=True)
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    address = models.TextField(null=True)
    apartment = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    pincode = models.CharField(max_length=10, null=True)
    phone = models.CharField(max_length=15, null=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.status}"


    
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

class Order(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Order Confirmed"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.CASCADE, related_name="orders", null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_date = models.DateField(null=True, blank=True)  # Estimated delivery date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")  # Order status
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if self.estimated_delivery_date and self.estimated_delivery_date < now().date():
            raise ValidationError({"estimated_delivery_date": "Estimated delivery date cannot be in the past."})

    def save(self, *args, **kwargs):
        """ Runs validation before saving """
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - {self.get_status_display()}"

    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} for Order {self.order.id}"



class ContactForm(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15)
    message = models.TextField()

    def __str__(self):
        return self.name



