from django.db import models
from datetime import timedelta
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.timezone import now
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.template.loader import get_template
from xhtml2pdf import pisa


from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from admin_panel.models import Message
from photobooths.models import Photobooth, Favorite
from reservations.models import Reservation, Invoice
from .models import Notification

from .forms import CustomUserCreationForm, ProfileUpdateForm, PasswordResetWithoutOldForm
from .serializers import PhotoboothSerializer

from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from accounts.models import Devis, Facture
from admin_panel.models import Accessory 
import uuid
from django.http import HttpResponseForbidden


CustomUser = get_user_model()


# Authentification

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # Sécurité : flags sensibles
            user.is_active = False  # Sécurité : compte inactif tant qu'il n'est pas validé
            user.is_staff = False
            user.is_superuser = False
            
            # remplit les champs CustomUser
            user.account_type = form.cleaned_data['account_type']
            user.phone_number = form.cleaned_data.get('phone_number')
            user.address = form.cleaned_data.get('address')

            # Champs entreprise
            if user.account_type == "company":
                user.company_name = form.cleaned_data.get('company_name')
                user.company_vat_number = form.cleaned_data.get('company_vat_number')
                user.company_address = form.cleaned_data.get('company_address')

            user.save()


            # Génération du lien d'activation
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            activation_link = request.build_absolute_uri(
                reverse('accounts:activate_account', kwargs={'uidb64': uid, 'token': token})
            )

            # Envoi email
            send_mail(
                subject="Activation de votre compte",
                message=(
                    f"Bonjour {user.username},\n\n"
                    f"Merci pour votre inscription !\n"
                    f"Cliquez sur ce lien pour activer votre compte :\n{activation_link}\n\n"
                    f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
                ),
                from_email="noreply@monsite.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Compte créé ! Vérifiez vos emails pour activer votre compte."
            )
            return redirect("accounts:login")

    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Vérification du token
    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter."
        )
        return redirect('accounts:login')

    messages.error(request, "Le lien d'activation est invalide ou expiré.")
    return redirect('register')


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()

        # Connexion
        login(self.request, user)
        messages.success(self.request, "Connexion réussie !")

        # Redirection ADMIN
        if user.is_staff or user.is_superuser:
            return redirect('admin_panel:admin_dashboard')

        # ENTREPRISE
        if user.account_type == "company":
            return redirect('accounts:entreprise_dashboard')

        # Redirection utilisateur normal
        return redirect('accounts:user_dashboard')


def logout_view(request):
    user = request.user
    logout(request)

    # Redirection personnalisée selon le rôle
    if user.is_staff or user.is_superuser:
        return render(
            request,
            'admin_panel/logout.html',
            {'message': "Vous avez été déconnecté du panneau d’administration."}
        )

    return render(
        request,
        'accounts/logout_success.html',
        {'message': "Vous avez été déconnecté."}
    )

# Profile Utilisateur

@login_required
def profile(request):
    user = request.user

    if user.account_type == "company":
        return redirect("accounts:entreprise_dashboard")

    return render(request, 'accounts/profile.html', {"user": user})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        print("POST DATA:",request.POST)
        form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")

            dashboard = 'accounts:entreprise_dashboard' if request.user.account_type == "company" else 'accounts:user_dashboard'
            return redirect(dashboard)

        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class CustomPasswordResetView(View):
    template_name = 'accounts/change_password.html'

    def get(self, request):
        form = PasswordResetWithoutOldForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PasswordResetWithoutOldForm(request.POST)

        if form.is_valid():
            form.save(request.user)
            messages.success(request, "Votre mot de passe a été mis à jour.")
            return redirect('password_change_done')

        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        return render(request, self.template_name, {'form': form})


@login_required
def request_account_deletion(request):
    user = request.user

    if user.deleted_at:
        messages.warning(request, "Votre compte est déjà en attente de suppression.")
    else:
        # Suppression programmée dans 30 jours
        user.deleted_at = timezone.now() + timedelta(days=30)
        user.save()
        messages.success(
            request,
            "Votre compte sera supprimé définitivement dans 30 jours. "
            "Vous pouvez annuler cette action avant la date limite."
        )

    return redirect('accounts:user_dashboard')


@login_required
def cancel_account_deletion(request):
    user = request.user

    if user.deleted_at:
        user.deleted_at = None
        user.save()
        messages.success(request, "La suppression de votre compte a été annulée.")
    else:
        messages.info(request, "Votre compte n'était pas en cours de suppression.")

    return redirect('accounts:user_dashboard')


def account_protection_notice(request):
    return render(request, "accounts/account_protection_notice.html")

# Tableau de bord utilisateur
@login_required
def user_dashboard(request):

    # Réservations de l'utilisateur
    reservations = request.user.reservations.all().order_by('-start_date')
   
    # Notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')


    # Factures paginées
    invoices = (
        Invoice.objects
        .filter(user=request.user)
        .prefetch_related('reservations')
        .order_by('-created_at')
    )

    paginator = Paginator(invoices, 5)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    
    # --- Comptage des statuts ---
    pending_count = reservations.filter(status="pending").count()
    confirmed_count = reservations.filter(status="confirmed").count()
    cancelled_count = reservations.filter(status=Reservation.CANCELED).count()


    return render(request, 'accounts/user_dashboard.html', {
        'reservations': reservations,
        'notifications': notifications,
        'page_obj': page_obj,
        'today': now().date(),
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'cancelled_count': cancelled_count,
    })

# Contact admin

User = get_user_model()

@login_required
def user_messages(request):
    # Messages envoyés ou reçus par l'utilisateur
    messages_list = (
        Message.objects.filter(recipient=request.user)
        | Message.objects.filter(sender=request.user)
    ).order_by('-created_at')

    unread_messages_count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    success = False

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not subject or not body:
            messages.error(request, "Veuillez remplir tous les champs.")
        else:
            admin = User.objects.filter(is_staff=True).first()

            if admin:
                Message.objects.create(
                    sender=request.user,
                    recipient=admin,
                    subject=subject,
                    body=body
                )
                messages.success(request, "Message envoyé à l’administrateur.")
                success = True
            else:
                messages.error(request, "Aucun administrateur disponible.")

    return render(request, 'accounts/user_messages.html', {
        'messages_list': messages_list,
        'unread_messages_count': unread_messages_count,
        'success': success,
    })


def contact_admin(request):
    return HttpResponse("Page de contact admin en construction")


# Favoris photobooth

@login_required
def user_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("photobooth")
    return render(request, "accounts/user_favorites.html", {"favorites": favorites})


@login_required
def toggle_favorite(request, photobooth_id):
    photobooth = get_object_or_404(Photobooth, id=photobooth_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        photobooth=photobooth
    )

    if not created:
        favorite.delete()

    return redirect(request.META.get("HTTP_REFERER", "accounts:user_dashboard"))

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Accès interdit")
    
    return render(request, "accounts/admin_dashboard.html")

# Redirections simples

def home(request):
    return render(request, 'home.html')


def profile_view(request):
    return render(request, 'accounts/profile.html')


def redirect_to_password_reset(request):
    return redirect(reverse('password_reset_custom'))


def set_language_ajax(request):
    return HttpResponse("Set language AJAX endpoint")


# RGPD — anonymisation utilisateur

def rgpd_delete_user(user):
    """Anonymise un utilisateur et ses données liées pour respecter le RGPD."""
    user.anonymize()

    # Anonymisation des factures
    for invoice in user.invoices.all():
        invoice.first_name = f"deleted_{user.id}"
        invoice.last_name = f"deleted_{user.id}"
        invoice.email = f"deleted_{user.id}@deleted.local"
        invoice.phone_number = None
        invoice.save()

    # Annulation des réservations
    for reservation in user.reservations_linked.all():
        reservation.status = Reservation.CANCELED
        reservation.save()


@login_required
def delete_account(request):
    if request.method == "POST":
        rgpd_delete_user(request.user)
        logout(request)
        return redirect("account_deleted")

    return render(request, 'delete_account_confirmation.html')

@login_required
def generate_invoice(request, reservation_id):
    try:
        # Sécurité : empêcher l'accès à la réservation d'un autre utilisateur
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

        # Si c'est une entreprise → créer un devis automatiquement
        if reservation.user.account_type == "company":
            devis = Devis.objects.create(
                user=reservation.user,
                numero=f"DEV-{uuid.uuid4().hex[:8].upper()}",
                description=f"Location Photobooth - {reservation.photobooth.name}",
                duree=1,
                prix_ht=float(reservation.photobooth.price),
                tva=21,
                prix_ttc=float(reservation.photobooth.price) * 1.21,
                company_name=reservation.user.company_name,
                company_address=reservation.user.company_address,
                company_vat_number=reservation.user.company_vat_number,
            )

        # Vérification du statut
        if reservation.status != Reservation.CONFIRMED:
            return HttpResponse(
                "La réservation doit être confirmée pour générer une facture.",
                status=400
            )

        # Création de la facture si elle n'existe pas
        if not reservation.invoice:
            invoice = Invoice.objects.create(
                user=reservation.user,
                total_amount=reservation.photobooth.price,
            )
            reservation.invoice = invoice
            reservation.save()
        else:
            invoice = reservation.invoice

        # Application d’un coupon éventuel
        if hasattr(reservation, 'coupon') and reservation.coupon:
            invoice.apply_coupon(reservation.coupon)

        # Calculs
        prix_initial = float(reservation.photobooth.price)
        prix_total = float(invoice.total_amount)
        discount = max(0.0, prix_initial - prix_total)

        # Création du PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50

        # Titre
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "FACTURE DE RÉSERVATION")

        # Date + numéro
        y -= 20
        now_dt = timezone.now()
        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Date : {now_dt.strftime('%d/%m/%Y %H:%M')}")
        p.drawRightString(width - 50, y, f"Facture n° {now_dt.strftime('%Y%m%d%H%M%S')}-{reservation.id}")

        # Ligne
        y -= 15
        p.line(50, y, width - 50, y)

        # Infos société
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Émetteur :")
        p.setFont("Helvetica", 10)

        societe_infos = [
            "Idealbooth SARL",
            "N° TVA : N TVA 12345678900978",
            "Tél : +32 465 45 67 89",
            "Email : bpgloire@gmail.com",
            "Adresse : 123 Rue des Lumières, 6000 Charleroi, Belgique"
        ]

        for line in societe_infos:
            y -= 15
            p.drawString(60, y, line)

        # Infos client
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Destinataire :")
        p.setFont("Helvetica", 10)

        user_name = reservation.user.get_full_name() or reservation.user.username
        client_infos = [
            f"Nom : {user_name}",
            f"Email : {reservation.user.email or 'Non fourni'}",
            f"Tél : {getattr(reservation.user, 'phone_number', 'Non fourni')}",
            f"Adresse : {getattr(reservation.user, 'address', 'Non fournie')}"
        ]

        for line in client_infos:
            y -= 15
            p.drawString(60, y, line)

        # Détails réservation
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Détails de la réservation")
        p.setFont("Helvetica", 10)

        details = [
            f"Photobooth : {reservation.photobooth.name}",
            f"Type d'événement : {reservation.event_type}",
            f"Date de début : {reservation.start_date.strftime('%d/%m/%Y')}",
            f"Date de fin : {reservation.end_date.strftime('%d/%m/%Y')}",
        ]

        for line in details:
            y -= 15
            p.drawString(60, y, line)

        # Accessoires éventuels
        if hasattr(reservation, 'accessories') and reservation.accessories.exists():
            accessoires_list = ", ".join(acc.name for acc in reservation.accessories.all())
            y -= 15
            p.drawString(60, y, f"Accessoires : {accessoires_list}")

        # Ligne montants
        y -= 20
        p.line(50, y, width - 50, y)

        # Montants
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Montant")

        p.setFont("Helvetica", 10)
        y -= 15
        p.drawString(60, y, f"Prix initial : {prix_initial:.2f} €")

        if discount > 0:
            y -= 15
            p.drawString(60, y, f"Réduction appliquée : {discount:.2f} € ({(discount/prix_initial)*100:.0f}%)")

        y -= 15
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, f"Prix TTC : {prix_total:.2f} €")

        # Remerciement
        y -= 30
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, y, "Merci pour votre confiance et votre réservation !")

        # Finalisation PDF
        p.save()
        buffer.seek(0)

        return FileResponse(buffer, as_attachment=True, filename=f"facture_{reservation.id}.pdf")

    except Reservation.DoesNotExist:
        return HttpResponse("Réservation introuvable.", status=404)

    except Exception as e:
        return HttpResponse(f"Une erreur est survenue : {str(e)}", status=500)

   
@login_required
def cancel_reservation(request, pk):
    reservation = get_object_or_404(Reservation, id=pk, user=request.user)

    reservation.status = "cancelled"
    reservation.save()

    messages.success(request, "Votre réservation a été annulée.")
    return redirect("accounts:user_dashboard")

@login_required
def generer_devis(request):
    user = request.user

    if user.account_type != "company":
        return redirect("profile")
    
    reservation = Reservation.objects.filter(user=user).order_by('-start_date').first()
    if not reservation:
        return HttpResponse("Aucune réservation trouvée.", status=404)

    photobooth = reservation.photobooth


    numero = f"DEV-{uuid.uuid4().hex[:8].upper()}"

    prix_ht = 250
    tva = 21
    prix_ttc = prix_ht + (prix_ht * tva / 100)

    # TON ENTREPRISE (IdealBooth)
    company_name = "IdealBooth"
    company_address = "123 Rue des Lumières, 6000 Charleroi, Belgique"
    company_phone="+32 465 288 647"
    company_email="contact@idealbooth.be"
    company_bce="BE 0254.160.091"
    company_vat_number="BE123456789"

    # ENTREPRISE CLIENT (Genesis)
    client_name = user.company_name
    client_address = user.company_address
    client_vat_number = user.company_vat_number
    

    devis = Devis.objects.create(
        user=user,
        numero=numero,
        reservation=reservation,
        # TON ENTREPRISE
        company_name=company_name,
        company_address=company_address,
        company_phone=company_phone,
        company_email=company_email,
        company_bce=company_bce,
        company_vat_number=company_vat_number,


        # CLIENT
        client_name=client_name,
        client_address=client_address,
        client_vat_number=client_vat_number,

        # PRESTATION
        prix_ht=prix_ht,
        tva=tva,
        prix_ttc=prix_ttc,
    )

    return render(request, "accounts/devis_detail.html",{
                "devis": devis,
                "event_date": reservation.start_date if reservation else None,
                "photobooth": photobooth,})

@login_required
def devis_pdf(request, devis_id):
    devis = get_object_or_404(Devis, id=devis_id, user=request.user)

    reservation = devis.reservation
    photobooth = reservation.photobooth if reservation else None
    event_date = reservation.start_date if reservation else None

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 40

    # TITRE
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Devis Photobooth - {devis.numero}")

    y -= 18
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Date : {devis.date_creation.strftime('%d/%m/%Y')}")

    y -= 10
    p.line(50, y, width - 50, y)

    # ENTREPRISE
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Informations Entreprise")

    p.setFont("Helvetica", 10)
    infos = [
        f"Nom : {devis.company_name}",
        f"Adresse : {devis.company_address or 'Non fournie'}",
        f"Téléphone : {devis.company_phone or 'Non fourni'}",
        f"E-mail : {devis.company_email or 'Non fourni'}",
        f"N° d'entreprise (BCE) : {devis.company_bce or 'Non fourni'}",
        f"TVA : {devis.company_vat_number or 'Non fournie'}",
    ]

    for line in infos:
        y -= 12
        p.drawString(60, y, line)

    # CLIENT
    y -= 22
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Informations Client")

    p.setFont("Helvetica", 10)
    client_infos = [
        f"Nom : {devis.client_name}",
        f"Adresse : {devis.client_address or 'Non fournie'}",
        f"TVA : {devis.client_vat_number or 'Non fournie'}",
    ]

    for line in client_infos:
        y -= 12
        p.drawString(60, y, line)

    # TABLEAU DES DÉTAILS
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Détails de la prestation")

    y -= 15
    p.setFont("Helvetica", 10)

    fonds_ecran_noms = "Non fourni"
    accessoires_noms = "Non fourni"

    if photobooth:
        fonds_ecran = Accessory.objects.filter(photobooth=photobooth, category='fond_ecran')
        if fonds_ecran.exists():
            fonds_ecran_noms = ", ".join(acc.name for acc in fonds_ecran)

        accessoires = Accessory.objects.filter(photobooth=photobooth, category='accessoire')
        if accessoires.exists():
            accessoires_noms = ", ".join(acc.name for acc in accessoires)

    details = [
        ("Date de l'événement :", event_date.strftime('%d/%m/%Y') if event_date else "Non fournie"),
        ("Lieu d'installation :", devis.client_address),
        ("Photobooth :", photobooth.name if photobooth else "Non fourni"),
        ("Description :", photobooth.description if photobooth else devis.description),
        ("Durée :", f"{devis.duree} jour{'s' if devis.duree > 1 else ''}"),
        ("Fonds d'écran inclus :", fonds_ecran_noms),
        ("Accessoires inclus :", accessoires_noms),
    ]

    col_label_x = 60
    col_value_x = 200
    max_width = 350  # largeur max pour retour ligne

    for label, value in details:
        y -= 18
        p.setFont("Helvetica-Bold", 10)
        p.drawString(col_label_x, y, label)

        p.setFont("Helvetica", 10)

        # Retour ligne automatique
        words = value.split(" ")
        line = ""
        for word in words:
            test_line = line + word + " "
            if p.stringWidth(test_line, "Helvetica", 10) < max_width:
                line = test_line
            else:
                y -= 14
                p.drawString(col_value_x, y, line)
                line = word + " "
        y -= 14
        p.drawString(col_value_x, y, line)

    # TABLEAU TARIFS
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Tarification")

    y -= 18

    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, y, "Description")
    p.drawString(250, y, "Qté")
    p.drawString(300, y, "PU HTVA")
    p.drawString(380, y, "Total HTVA")

    y -= 5
    p.line(50, y, width - 50, y)

    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(60, y, photobooth.name if photobooth else "Photobooth")
    p.drawString(250, y, "1")
    p.drawString(300, y, f"{devis.prix_ht} €")
    p.drawString(380, y, f"{devis.prix_ht} €")

    # TOTALS
    tva_amount = (devis.prix_ht * devis.tva) / 100

    y -= 25
    p.setFont("Helvetica-Bold", 10)
    p.drawString(300, y, "Sous-total HTVA :")
    p.drawString(420, y, f"{devis.prix_ht} €")

    y -= 15
    p.drawString(300, y, f"TVA ({devis.tva}%) :")
    p.drawString(420, y, f"{tva_amount:.2f} €")

    y -= 15
    p.drawString(300, y, "TOTAL TVAC :")
    p.drawString(420, y, f"{devis.prix_ttc} €")

    # CONDITIONS
    y -= 55
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Conditions spécifiques à la location")

    p.setFont("Helvetica", 10)
    conditions = [
        "Le règlement de la présente prestation a été reçu et validé.",
        "La réservation est confirmée à compter de la réception du paiement.",
        f"Plages horaires : Mise à disposition le {event_date.strftime('%d/%m/%Y') if event_date else '---'}.",
        "Responsabilité : Le client assure la sécurité du photobooth et des accessoires.",
        "Le client est responsable des dégradations ou pertes causées au matériel mis à disposition pendant la durée de l'événement.",
        "Le matériel sera installé et récupéré par IdealBooth aux dates convenues."
    ]

    for line in conditions:
        y -= 12
        p.drawString(60, y, line)

    # Devis accepter
    y -= 25
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Devis")

    p.setFont("Helvetica", 10)
    y -= 18
    p.drawString(60, y, "Devis accepté et réglé électroniquement via Stripe ")

    p.save()
    buffer.seek(0)

    return FileResponse(buffer, as_attachment=True, filename=f"devis_{devis.numero}.pdf")

@login_required
def entreprise_dashboard(request):
    user = request.user  # Ton CustomUser

    # Vérification du type de compte
    if user.account_type != "company":
        return HttpResponseForbidden("Accès réservé aux entreprises.")

    # Récupération des devis de l'entreprise
    devis = Devis.objects.filter(user=user).order_by("-date_creation")

    # Récupération des factures de l'entreprise
    factures = Facture.objects.filter(user=user).order_by("-date_creation")

    return render(request, "accounts/entreprise_dashboard.html", {
        "user": user,
        "devis": devis,
        "factures": factures,  
    })


@login_required
def entreprise_reservations(request):
    user = request.user

    if user.account_type != "company":
        return HttpResponseForbidden("Accès réservé aux entreprises.")

    reservations = Reservation.objects.filter(user=user)

    return render(request, "accounts/entreprise_reservations.html", {
        "reservations": reservations
    })


@login_required
def devis_list(request):
    devis = Devis.objects.filter(user=request.user)
    return render(request, "accounts/devis/devis_list.html", {"devis": devis})


@login_required
def devis_detail(request, pk):
    devis = get_object_or_404(Devis, pk=pk, user=request.user)
    return render(request, "accounts/devis/devis_detail.html", {"devis": devis})

@login_required
def devis_create(request):
    # Sécurité : accès réservé aux entreprises
    if request.user.account_type != "company":
        return HttpResponseForbidden("Accès réservé aux entreprises.")

    if request.method == "POST":
        montant = request.POST.get("montant")
        
        idealbooth = User.objects.get(username="IdealBooth")

        devis = Devis.objects.create(
            entreprise=idealbooth,   # ← TOUJOURS IdealBooth
            client=request.user,     # ← l’utilisateur connecté
            prix_ht=montant,
            prix_ttc=float(montant) * 1.21,
            tva=21,
            description="Devis créé manuellement",
            duree=1,
        )

        return redirect("accounts:devis_list")

    return render(request, "accounts/devis_create.html")


@login_required
def company_info(request):
    user = request.user

    if user.account_type != "company":
        return HttpResponseForbidden("Accès réservé aux entreprises.")

    if request.method == "POST":
        user.company_name = request.POST.get("company_name")
        user.company_vat_number = request.POST.get("company_vat_number")
        user.company_address = request.POST.get("company_address")
        user.save()

        messages.success(request, "Informations entreprise mises à jour.")
        return redirect("accounts:company_info")

    return render(request, "accounts/company_info.html", {
        "user": user
    })

@login_required
def factures_list(request):
    user = request.user

    if user.account_type != "company":
        return HttpResponseForbidden("Accès réservé aux entreprises.")

    factures = Facture.objects.filter(user=user)

    return render(request, "accounts/factures_list.html", {
        "factures": factures
    })

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Facture, pk=pk, user=request.user)
    return render(request, "accounts/invoice_pdf.html", {"invoice": invoice})

@login_required
def invoice_detail(request, pk):
    invoice = Facture.objects.get(pk=pk)

    if request.user != invoice.user:
        return HttpResponseForbidden("Accès refusé.")

    return render(request, "accounts/invoice_detail.html", {
        "invoice": invoice
    })

@login_required
def valider_devis(request, devis_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("Accès interdit")
    
    devis = get_object_or_404(Devis, id=devis_id)

    # Mise à jour du statut
    devis.status = "accepted"
    devis.save()

    # Création automatique de la facture entreprise
    Facture.objects.create(
        devis=devis,
        user=devis.compagny,
        numero=f"FAC-{devis.numero}",
        montant_ht=devis.prix_ht,
        montant_ttc=devis.prix_ttc,
    )

    messages.success(request, "Le devis a été validé et la facture a été générée.")
    return redirect("accounts:admin_dashboard")

@login_required
def admin_devis_list(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Accès interdit")
    
    devis = Devis.objects.all().order_by("-date_creation")
    return render(request, "admin_panel/admin_devis_list.html", {"devis": devis})

def admin_read_notification(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Accès interdit")
    
    notif = get_object_or_404(Notification, pk=pk)
    notif.read = True
    notif.save()
    return redirect('accounts:admin_dashboard')

def admin_delete_notification(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Accès interdit")
    
    notif = get_object_or_404(Notification, pk=pk)
    notif.delete()
    return redirect('accounts:admin_dashboard')

def delete_notification(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.delete()
    return redirect('accounts:user_dashboard')

@login_required
def conversation_detail(request, pk):
    # Message principal
    root = get_object_or_404(Message, pk=pk, recipient=request.user)

    # Tous les messages du thread (message principal + réponses)
    thread = Message.objects.filter(
        models.Q(pk=pk) | models.Q(parent=root)
    ).order_by('created_at')

    # Marquer comme lus
    thread.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, "accounts/conversation_detail.html", {
        "root": root,
        "thread": thread
    })

from django.db.models import Q

@login_required
def user_messages(request):
    
    # Trouver l'admin
    admin_user = CustomUser.objects.filter(is_staff=True).first()

    # Messages entre l'utilisateur et l'admin
    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=admin_user)) |
        (Q(sender=admin_user) & Q(recipient=request.user))
    ).order_by('-created_at')

    # Marquer comme lus
    Message.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    # Réponse à un message
    if request.method == "POST":
        parent_id = request.POST.get("parent_id")
        body = request.POST.get("body")

        if not parent_id:
            Message.objects.create(
                sender=request.user,
                recipient=admin_user,
                subject="Nouveau message",
                body=body
            )
            return redirect('accounts:user_messages')
        
        parent = get_object_or_404(Message, pk=parent_id, recipient=request.user)

        Message.objects.create(
            sender=request.user,
            recipient=parent.sender,
            subject="Re: " + parent.subject,
            body=body,
            parent=parent
        )

        return redirect('accounts:user_messages')

    return render(request, "accounts/user_messages.html", {
        "messages_list": messages_list
    })
