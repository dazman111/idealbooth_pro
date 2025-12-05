from rest_framework import viewsets, permissions
from .models import Reservation
from .serializers import ReservationSerializer
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Invoice
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import render, redirect
from django.contrib import messages
from coupons.models import Coupon
import stripe
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

# Si tu veux vraiment une vue admin différente, tu peux faire :
class AdminReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        # Récupérer la réservation avec l'ID fourni
        reservation = self.get_object()

        # Vérifier que l'utilisateur est admin ou est le propriétaire de la réservation
        if request.user.is_staff or reservation.user == request.user:
            # Vérifier que la réservation n'est pas déjà annulée
            if reservation.status == Reservation.CANCELED:
                return Response({"detail": "Cette réservation est déjà annulée."}, status=400)

            # Mettre à jour le statut de la réservation à 'canceled'
            reservation.status = Reservation.CANCELED
            reservation.save()

            return Response({"detail": "Réservation annulée avec succès."})
        else:
            return Response({"detail": "Vous n'avez pas les droits pour annuler cette réservation."}, status=403)

def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)

    html_string = render_to_string('invoices/invoice.html', {'invoice': invoice})


    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="facture_{invoice.id}.pdf"'

    return response

def checkout(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id, user=request.user)

    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code", "").strip()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if invoice.apply_coupon(coupon):
                    messages.success(request, f"Coupon {coupon.code} appliqué avec succès.")
                    request.session['coupon_id'] = coupon.id
                else:
                    messages.error(request, "Coupon invalide ou expiré.")
            except Coupon.DoesNotExist:
                messages.error(request, "Ce coupon n'existe pas.")

    return render(request, "checkout.html", {"invoice": invoice})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # --- Gestion de l'événement : payment réussi ---
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        try:
            invoice = Invoice.objects.get(stripe_checkout_session_id=session["id"])
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'Invoice not found'}, status=404)

        invoice.payment_status = 'paid'
        invoice.stripe_payment_intent_id = session.get("payment_intent")
        invoice.save(update_fields=['payment_status', 'stripe_payment_intent_id'])

    return JsonResponse({'status': 'success'})


