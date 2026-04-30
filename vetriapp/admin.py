from django.contrib import admin
from . models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Product)

admin.site.register(BillingAddress)
admin.site.register(PaymentTransaction)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(ContactForm)
