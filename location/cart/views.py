# cart/views.py 
import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from decimal import Decimal, InvalidOperation

import stripe

from .models import Cart, CartItem
from .forms import AddToCartForm  # si tu l'utilises ailleurs
from photobooths.models import Photobooth  # et si tu as PhotoboothOption : , PhotoboothOption
from reservations.models import Reservation, Invoice
from coupons.models import Coupon
from django.core.mail import send_mail  # Si tu veux envoyer un e-mail aussi, sinon tu peux omettre cette importation
from accounts.models import Notification
from reservations.models import Notification

  # Importation du modèle Notification


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()


# -------------------------
# Fonctions de gestion du panier
# -------------------------

@login_required
def add_to_cart(request, photobooth_id):
    photobooth = get_object_or_404(Photobooth, id=photobooth_id)

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Requête invalide."}, status=200)

    try:
        quantite = int(request.POST.get('quantite', 1))
        if quantite <= 0:
            raise ValueError
    except ValueError:
        return JsonResponse({"success": False, "message": "Quantité invalide."}, status=200)

    try:
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({"success": False, "message": "Dates invalides ou manquantes."}, status=200)

    if end_date < start_date:
        return JsonResponse({"success": False, "message": "La date de fin doit être après la date de début."}, status=200)
    if start_date < date.today():
        return JsonResponse({"success": False, "message": "La date de début ne peut pas être dans le passé."}, status=200)

    # Vérification du stock
    total_reserved = Reservation.objects.filter(
        photobooth=photobooth,
        start_date__lte=end_date,
        end_date__gte=start_date,
        status=Reservation.CONFIRMED
    ).aggregate(total=Sum('quantity'))['total'] or 0

    existing_item = CartItem.objects.filter(
        cart__user=request.user,
        photobooth=photobooth,
        start_date=start_date,
        end_date=end_date
    ).first()
    user_existing_qty = existing_item.quantite if existing_item else 0

    total_in_other_carts = CartItem.objects.filter(
        photobooth=photobooth,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).exclude(cart__user=request.user).aggregate(total=Sum('quantite'))['total'] or 0

    disponible = photobooth.stock - total_reserved - total_in_other_carts
    if disponible <= 0:
        return JsonResponse({"success": False, "message": "Ce photobooth est indisponible pour ces dates."}, status=200)

    max_possible = disponible - user_existing_qty
    if quantite > max_possible:
        if max_possible <= 0:
            return JsonResponse({"success": False, "message": "Aucune unité supplémentaire disponible."}, status=200)
        quantite = max_possible
        msg = f"Seules {quantite} unité(s) ont été ajoutées en raison du stock limité."
    else:
        msg = "Article ajouté au panier avec succès !"

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        photobooth=photobooth,
        start_date=start_date,
        end_date=end_date,
        defaults={'quantite': quantite}
    )

    if not created:
        cart_item.quantite += quantite
        cart_item.save()
        msg = f"Quantité mise à jour à {cart_item.quantite} dans votre panier."

    # Calcul du nombre total d'articles dans le pa
    # Vérifie si la requête est AJAX
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # c’est AJAX → on renvoie du JSON
        cart_count = CartItem.objects.filter(cart=cart).aggregate(total=Sum('quantite'))['total'] or 0
        return JsonResponse({
            "success": True,
            "message": msg,
            "cart_count": cart_count
        }, status=200)

    # sinon, ce n’est pas AJAX → redirige vers la page HTML
    # sinon, si ce n’est pas AJAX, on reste sur la page photobooth avec message
    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'photobooths'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Article retiré du panier.")
    return redirect('cart_detail')


@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            quantite = int(request.POST.get('quantite', 1))
            type_evenement = request.POST.get('type_evenement', 'mariage')

            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            if start_date_str and end_date_str:
                new_start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                new_end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
                new_end_dt = new_end_dt.replace(hour=23, minute=59, second=59)

                if new_end_dt < new_start_dt:
                    return JsonResponse({'success': False, 'error': "La date de fin ne peut pas être antérieure à la date de début."})

                conflit_reservation = Reservation.objects.filter(
                    photobooth=item.photobooth,
                    start_date__lte=new_end_dt,
                    end_date__gte=new_start_dt
                ).exists()

                conflit_cartitem = CartItem.objects.filter(
                    cart=item.cart,
                    photobooth=item.photobooth,
                    start_date__lte=new_end_dt.date(),
                    end_date__gte=new_start_dt.date()
                ).exclude(id=item.id).exists()

                if conflit_reservation or conflit_cartitem:
                    return JsonResponse({'success': False, 'error': "Ce photobooth est déjà réservé sur cette période."})

                item.start_date = new_start_dt.date()
                item.end_date = new_end_dt.date()

            item.quantite = quantite
            item.type_evenement = type_evenement
            item.save()

            # Renvoie le nouveau nombre d'articles dans le panier
            cart_count = item.cart.items.count

            return JsonResponse({'success': True, 'cart_count': cart_count, 'message': "Article mis à jour avec succès."})
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f"Erreur lors de la mise à jour de l’article : {str(e)}"})

    # Si pas POST ou pas AJAX
    return JsonResponse({'success': False, 'error': 'Requête invalide.'})

@login_required
def cart_detail(request):
    print(f"User {request.user} is authenticated")

    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.refresh_from_db()

    # Si le coupon du panier a déjà été utilisé par cet utilisateur => le retirer
    if cart.coupon and hasattr(cart.coupon, 'users_used') and request.user in cart.coupon.users_used.all():
        cart.coupon = None
        cart.save()
        messages.warning(request, "Ce code promo a déjà été utilisé et a été retiré de votre panier.")

    # Vérifier la validité temporelle du coupon
    if cart.coupon:
        now = timezone.now()
        # gère si date_debut/date_fin sont des date ou datetime
        date_debut = getattr(cart.coupon, 'date_debut', None)
        date_fin = getattr(cart.coupon, 'date_fin', None)
        if (date_debut and date_debut > now) or (date_fin and date_fin < now):
            cart.coupon = None
            cart.save()
            messages.warning(request, "Le coupon n'est plus valide et a été retiré du panier.")

    subtotal = cart.get_total_without_discount()
    discount = cart.get_discount()
    final_total = cart.get_total_price()

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'final_total': final_total,
        'coupon': cart.coupon,
        'STRIPE_PUBLISHABLE_KEY': settings.STRIPE_PUBLISHABLE_KEY,
    })

def clear_cart(request):
    CartItem.objects.filter(user=request.user).delete()
    request.session.pop('coupon_id', None)
    return redirect('cart_detail')


# -------------------------
# Paiement / Stripe
# -------------------------
@login_required
def checkout(request):
    messages.warning(request, "La page de checkout directe n'est plus utilisée. Veuillez passer par le panier.")
    return redirect('cart_detail')


@login_required
@require_POST
def create_checkout_session(request):
    user = request.user
    cart = Cart.objects.filter(user=user).first()

    if not cart or not cart.items.exists():
        return JsonResponse({'error': 'Votre panier est vide.'}, status=400)

    # Total après réduction (assure-toi que get_total_price renvoie Decimal)
    total_after_discount = Decimal(cart.get_total_price())
    unit_amount_cents = int((total_after_discount * Decimal('100')).to_integral_value(rounding=ROUND_HALF_UP))

    if unit_amount_cents <= 0:
        return JsonResponse({'error': 'Le montant du panier est invalide.'}, status=400)

    line_items = [{
        'price_data': {
            'currency': 'eur',
            'product_data': {'name': f'Panier de {cart.user.username}'},
            'unit_amount': unit_amount_cents,
        },
        'quantity': 1,
    }]

    try:
        with transaction.atomic():
            invoice = Invoice.objects.create(
                user=user,
                total_amount=total_after_discount,
                payment_status='pending',
                # Si ton modèle Invoice possède un champ coupon_used (FK vers Coupon)
                coupon_used=cart.coupon if getattr(cart, 'coupon', None) else None
            )

            # Créer chaque réservation liée à la facture
            for item in cart.items.all():
                Reservation.objects.create(
                    user=user,
                    photobooth=item.photobooth,
                    start_date=datetime.combine(item.start_date, datetime.min.time()),
                    end_date=datetime.combine(item.end_date, datetime.max.time()),
                    status=Reservation.PENDING,
                    invoice=invoice,
                    quantity=item.quantity if hasattr(item, "quantity") else 1

                )

            # Création de la session Stripe (on passe invoice_id en metadata)
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer_email=user.email,
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri(reverse('checkout_success')),
                cancel_url=request.build_absolute_uri('/panier/'),
                metadata={'invoice_id': str(invoice.id)},
            )

            # Sauvegarder éventuellement l'id de session (pratique pour debug)
            invoice.stripe_checkout_session_id = checkout_session.id
            invoice.save()

        return JsonResponse({'id': checkout_session.id})

    except Exception as e:
        logger.exception("Erreur création session Stripe")
        return JsonResponse({'error': f'Erreur lors de la création de la session Stripe : {str(e)}'}, status=500)

def payment_success(request):
    # On supprime le coupon une fois le paiement validé
    request.session.pop('coupon_id', None)
    return render(request, "cart/payment_success.html")

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception as e:
        print(" Signature invalide :", e)
        return HttpResponse(status=400)

    event_type = event["type"]
    print(" EVENT:", event_type)

    # Événements qui indiquent que le paiement est réussi
    payment_events = [
        "checkout.session.completed",
        "payment_intent.succeeded",
        "charge.succeeded",
    ]

    if event_type not in payment_events:
        return HttpResponse(status=200)

    try:
        data = event["data"]["object"]

        # On récupère la metadata selon le type d'événement
        if event_type == "checkout.session.completed":
            metadata = data.get("metadata", {})
        else:
            # pour payment_intent ou charge
            payment_intent_id = data["payment_intent"] if "payment_intent" in data else data["id"]
            pi = stripe.PaymentIntent.retrieve(payment_intent_id)
            metadata = pi.get("metadata", {})

        invoice_id = metadata.get("invoice_id")
        if not invoice_id:
            print(" Pas de metadata invoice_id")
            return HttpResponse(status=400)

        invoice = Invoice.objects.get(id=invoice_id)
        invoice.payment_status = "paid"
        invoice.save()

        # Confirmer toutes les réservations liées
        for r in invoice.reservation_set.all():
            r.status = Reservation.CONFIRMED
            r.save()
        
        # --- Notification admin ---
        admins = User.objects.filter(is_staff=True)  # tous les admins
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f" La réservation #{r.id} a été payée par {r.user.get_full_name()}."
            )

        print(" FACTURE + RÉSERVATIONS VALIDÉES + NOTIFICATION ADMIN :", invoice_id)

    except Exception as e:
        print(" ERREUR:", e)
        return HttpResponse(status=500)

    return HttpResponse(status=200)


@login_required
def checkout_success(request):
    """
    Vue appelée après redirection vers success_url (après paiement).
    On vide le panier côté session utilisateur (déjà géré au webhook mais on double-check ici).
    """
    try:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart.items.all().delete()
            cart.coupon = None
            cart.save()
    except Exception:
        logger.exception("Erreur lors du vidage du panier dans checkout_success")

    messages.success(request, "Paiement réussi ! Votre panier a été vidé.")
    return render(request, 'cart/checkout_success.html')


@login_required
def confirm_cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.warning(request, "Votre panier est vide. Veuillez ajouter des articles avant de confirmer.")
        return redirect('cart_detail')

    total_without_discount = cart.get_subtotal_price()
    discount = cart.get_discount()
    total_price = cart.get_total_price()

    return render(request, 'cart/confirm_cart.html', {
        'cart': cart,
        'total_without_discount': total_without_discount,
        'discount': discount,
        'total_price': total_price,
        "STRIPE_PUBLISHABLE_KEY": settings.STRIPE_PUBLISHABLE_KEY,
    })


def payment_success(request):
    messages.success(request, "Paiement réussi ! Votre commande est en cours de traitement.")
    return render(request, 'cart/payment_success.html')


# -------------------------
# Gestion des coupons (AJAX)
# -------------------------

@require_POST
def apply_coupon(request):
    code = request.POST.get("code", "").strip()
    current_subtotal = request.POST.get("current_subtotal")

    # Convertir proprement
    try:
        current_subtotal = float(current_subtotal)
    except:
        current_subtotal = 0.00

    if not code:
        return JsonResponse({
            "success": False,
            "message": "Veuillez entrer un code promo.",
            "subtotal": current_subtotal
        })

    # Chercher le coupon
    try:
        coupon = Coupon.objects.get(code__iexact=code)
    except Coupon.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Code promo invalide.",
            "subtotal": current_subtotal
        })

    # Vérifier validité
    if not coupon.est_valide():
        return JsonResponse({
            "success": False,
            "message": "Ce code promo n'est plus valide.",
            "subtotal": current_subtotal
        })

    # Calcul réduction
    remise = float(coupon.apply_discount(current_subtotal))
    new_total = current_subtotal - remise

    # Renvoie toutes les infos utiles au JS
    return JsonResponse({
        "success": True,
        "message": "Code appliqué avec succès.",
        "coupon_code": coupon.code,
        "discount_type": coupon.discount_type,      # "percent" ou "fixed"
        "discount_value": float(coupon.discount_value),  # ex : 10
        "discount_amount": remise,                 # ex : 52.50
        "subtotal": current_subtotal,
        "total": new_total
    })


@login_required
def remove_coupon(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.coupon = None
    cart.save()
    messages.info(request, "Le code promo a été retiré.")
    return redirect('cart_detail')


def get_cart_item_count(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        count = cart.items.count()
    else:
        count = 0
    return JsonResponse({'count': count})

def get_cart_item_count(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return JsonResponse({'count': count})

