from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

import stripe

from .forms import ReservationForm
from .models import Invoice, Reservation
from .serializers import ReservationSerializer
from coupons.models import Coupon
from admin_panel.models import Accessory

stripe.api_key = settings.STRIPE_SECRET_KEY

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AdminReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel_reservation(self, request, pk=None):
        reservation = self.get_object()

        if not (request.user.is_staff or reservation.user == request.user):
            return Response({"detail": "Accès refusé."}, status=403)

        if reservation.status == Reservation.CANCELED:
            return Response({"detail": "Déjà annulée."}, status=400)

        reservation.status = Reservation.CANCELED
        reservation.save()

        return Response({"detail": "Réservation annulée."})

class UserReservationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = Reservation.objects.filter(user=request.user)
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data["user"] = request.user.id

        serializer = ReservationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)
    
def create_reservation(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            return redirect('reservation_success')
    else:
        form = ReservationForm()

    return render(request, 'reservations/reservation_form.html', {'form': form})

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if reservation.start_date.date() <= date.today():
        messages.error(request, "Impossible d'annuler une réservation déjà commencée ou passée.")
        return redirect('user_reservations')

    if reservation.status == Reservation.CANCELED:
        messages.info(request, "Cette réservation est déjà annulée.")
        return redirect('user_reservations')

    reservation.status = Reservation.CANCELED
    reservation.save()

    messages.success(request, "Votre réservation a bien été annulée.")
    return redirect('user_reservations')

@login_required
def invoice_pdf(request, invoice_id):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from io import BytesIO
    from django.utils import timezone

    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    reservation = invoice.reservations.first()

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    # TITRE
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, "FACTURE DE RÉSERVATION")
    y -= 25

    now_dt = invoice.payment_date or timezone.now()
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Date : {now_dt.strftime('%d/%m/%Y %H:%M')}")
    p.drawRightString(width - 50, y, f"Facture n° {now_dt.strftime('%Y%m%d%H%M%S')}-{invoice.id}")
    y -= 10
    p.line(50, y, width - 50, y)
    y -= 25

    # ÉMETTEUR
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Émetteur :")
    y -= 15
    p.setFont("Helvetica", 10)
    emetteur = [
        "Idealbooth SARL",
        "N° TVA : BE 0254.160.091",
        "Tél : +32 465 288 647",
        "Email : contact@idealbooth.be",
        "Adresse : 123 Rue des Lumières, 6000 Charleroi, Belgique",
    ]
    for line in emetteur:
        p.drawString(60, y, line)
        y -= 14

    y -= 15

    # DESTINATAIRE
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Destinataire :")
    y -= 15
    p.setFont("Helvetica", 10)
    user_name = invoice.user.get_full_name() or invoice.user.username
    destinataire = [
        f"Nom : {user_name}",
        f"Email : {invoice.email or invoice.user.email or 'Non fourni'}",
        f"Tél : {invoice.phone_number or getattr(invoice.user, 'phone_number', 'Non fourni')}",
        f"Adresse : {invoice.address or getattr(invoice.user, 'address', 'Non fournie')}",
    ]
    for line in destinataire:
        p.drawString(60, y, line)
        y -= 14

    y -= 20
    p.line(50, y, width - 50, y)
    y -= 25

    # DÉTAILS DE LA RÉSERVATION
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Détails de la réservation")
    y -= 18

    p.setFont("Helvetica", 10)
    for reservation in invoice.reservations.all():
        details = [
            f"Photobooth : {reservation.photobooth.name}",
            f"Type d'événement : {reservation.get_event_type_display()}",
            f"Date de début : {reservation.start_date.strftime('%d/%m/%Y')}",
            f"Date de fin : {reservation.end_date.strftime('%d/%m/%Y')}",
        ]

        for line in details:
            p.drawString(60, y, line)
            y -= 14

        # Fonds d'écran inclus pour ce photobooth
        fonds_ecran = Accessory.objects.filter(
            photobooth=reservation.photobooth,
            category='fond_ecran'
        )
        if fonds_ecran.exists():
            noms = ", ".join(acc.name for acc in fonds_ecran)
            p.drawString(60, y, f"Fonds d'écran inclus : {noms}")
            y -= 14

        accessoires = Accessory.objects.filter(
        photobooth=reservation.photobooth,
        category='accessoire'
        )
        if accessoires.exists():
            noms = ", ".join(acc.name for acc in accessoires)
            p.drawString(60, y, f"Accessoires inclus : {noms}")
            y -= 14


        y -= 10

    if y < 150:
        p.showPage()
        y = height - 60
        p.setFont("Helvetica", 10)

        if y < 150:
            p.showPage()
            y = height - 60
            p.setFont("Helvetica", 10)

    y -= 10
    p.line(50, y, width - 50, y)
    y -= 25

    # MONTANT
    # MONTANT
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Montant")
    y -= 18
    p.setFont("Helvetica", 10)

    coupon = getattr(invoice, 'coupon_used', None)

    if coupon:
        # Calcul du sous-total avant réduction
        sous_total = invoice.total_amount
        if coupon.discount_type == 'percent':
            reduction = sous_total * (coupon.discount_value / 100)
            sous_total_avant = sous_total / (1 - (coupon.discount_value / 100))
        else:
            reduction = min(coupon.discount_value, sous_total)
            sous_total_avant = sous_total + reduction

        p.drawString(60, y, f"Sous-total : {sous_total_avant:.2f} €")
        y -= 14
        p.setFillColorRGB(0, 0.5, 0)
        p.drawString(60, y, f"Réduction ({coupon.code}) : -{reduction:.2f} €")
        p.setFillColorRGB(0, 0, 0)
        y -= 14
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, f"Total payé : {invoice.total_amount} €")
    else:
        p.drawString(60, y, f"Total : {invoice.total_amount} €")

    y -= 30

    # MERCI
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "Merci pour votre confiance et votre réservation !")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{invoice.id}.pdf"'
    return response

def checkout(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id, user=request.user)

    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code", "").strip()

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if invoice.apply_coupon(coupon):
                    messages.success(request, f"Coupon {coupon.code} appliqué.")
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
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return JsonResponse({'error': 'Invalid signature'}, status=400)

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

