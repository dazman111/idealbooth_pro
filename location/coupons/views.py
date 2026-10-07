from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from cart.models import Cart
from .models import Coupon


@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip()
    user = request.user

    if not code:
        return JsonResponse({'error': 'Veuillez entrer un code coupon.'}, status=400)

    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'error': 'Coupon invalide.'}, status=404)

    # Vérifier validité du coupon
    if not coupon.est_valide():
        return JsonResponse({'error': 'Ce coupon n’est plus valable ou a atteint sa limite d’utilisation.'}, status=400)

    # Récupérer le panier utilisateur
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return JsonResponse({'error': 'Panier introuvable.'}, status=404)

    # Appliquer coupon au panier
    cart.coupon = coupon
    cart.save()

    # Recalcul du total immédiatement
    subtotal = cart.get_subtotal_price()
    discount_amount = cart.get_discount()
    total_final = cart.get_total_price()

    return JsonResponse({
        'message': 'Coupon appliqué avec succès.',
        'discount_type': coupon.discount_type,         # percent OU fixed
        'discount_value': float(coupon.discount_value),  # valeur brute
        'discount_amount': float(discount_amount),       # montant réel appliqué
        'subtotal': float(subtotal),
        'total_final': float(total_final),
    })


@login_required
def remove_coupon(request):
    """Retirer un coupon du panier."""
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart.coupon = None
        cart.save()

    return JsonResponse({
        'message': 'Coupon retiré.',
        'subtotal': float(cart.get_subtotal_price()),
        'total_final': float(cart.get_total_price()),
    })
