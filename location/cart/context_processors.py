# cart/context_processors.py
from .models import CartItem, Cart
from django.db.models import Sum

def cart_count(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            count = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantite'))['total'] or 0
        else:
            count = 0
    else:
        count = 0

    return {'cart_count': count}
