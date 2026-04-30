from vetriapp.models import Cart

def cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()  # Counts unique products only
    return {'cart_count': cart_count}


from vetriapp.models import Category

def category_context(request):
    return {'banners': Category.objects.all()}
