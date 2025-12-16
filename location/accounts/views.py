from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Message
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.timezone import now
from datetime import timedelta
from django.views import View
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.conf import settings

from .forms import CustomUserCreationForm, ProfileUpdateForm, PasswordResetWithoutOldForm
from .serializers import PhotoboothSerializer

from photobooths.models import Photobooth, Favorite
from reservations.models import Reservation, Invoice

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly




# Authentification

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Génération du lien d'activation
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(
                reverse('activate_account', kwargs={'uidb64': uid, 'token': token})
            )

            # Envoi email
            send_mail(
                "Activation de votre compte",
                f"Bonjour {user.username},\n\nCliquez sur ce lien pour activer votre compte :\n{activation_link}",
                "noreply@monsite.com",
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "Compte créé ! Veuillez vérifier vos emails pour activer votre compte.")
            return redirect("login")
        
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.")
        return redirect('login')
    else:
        messages.error(request, "Le lien d'activation est invalide ou expiré.")
        return redirect('register')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(self.request, "Connexion réussie !")

        # ADMIN -> redirige vers admin_dashboard
        if user.is_staff or user.is_superuser:
            return redirect('admin_panel:admin_dashboard')  # Assure-toi que cette URL a name='admin_dashboard'

        # USER NORMAL -> redirige vers dashboard utilisateur
        return redirect('accounts:user_dashboard')  # Assure-toi que ton dashboard a name='dashboard'


def logout_view(request):
    user = request.user
    logout(request)

    if user.is_staff or user.is_superuser:
        # Admin : page spécifique avec message
        return render(request, 'admin_panel/logout_success_admin.html', {
            'message': "Vous avez été déconnecté du panneau d’administration."
        })
    else:
        # Utilisateur normal : page standard
        return render(request, 'accounts/logout_success.html', {
            'message': "Vous avez été déconnecté."
        })
    
# Profile Utilisateur
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('accounts:user_dashboard')
        else:
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
        return render(request, self.template_name, {'form': form})

@login_required
def request_account_deletion(request):
    user = request.user
    if user.deleted_at:
        messages.warning(request, "Votre compte est déjà en attente de suppression.")
    else:
        user.deleted_at = timezone.now() + timedelta(days=30)
        user.save()
        messages.success(request, "Votre compte sera supprimé définitivement dans 30 jours. Vous pouvez annuler avant cette date.")

    return redirect('user_dashboard')  # redirige vers le dashboard

@login_required
def cancel_account_deletion(request):
    user = request.user
    if user.deleted_at:
        user.deleted_at = None
        user.save()
        messages.success(request, "La suppression de votre compte a été annulée.")
    else:
        messages.info(request, "Votre compte n'était pas en suppression.")
    return redirect('user_dashboard')

def account_protection_notice(request):
    return render(request, "accounts/account_protection_notice.html")



# Tableau de bord utilisateur

@login_required(login_url='home')
def user_dashboard(request):
    invoices = Invoice.objects.filter(user=request.user).prefetch_related('reservations_linked').order_by('-created_at')
    paginator = Paginator(invoices, 5)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.page(1)

    return render(request, 'accounts/user_dashboard.html', {
        'page_obj': page_obj,
        'user': request.user,
        'today': now().date(),
    })



# Contact admin

User = get_user_model()

@login_required
def user_messages(request):
    messages_list = Message.objects.filter(
        recipient=request.user
    ) | Message.objects.filter(sender=request.user)
    messages_list = messages_list.order_by('-created_at')

    # Compter les messages non lus
    unread_messages_count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    success = False  # pour le template

    if request.method == 'POST':
        subject = request.POST.get('subject')
        body = request.POST.get('body')
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
        'success': success
    })

def contact_admin(request):
    return HttpResponse("Page de contact admin en construction")

# Favorie photobooth

@login_required
def user_favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related("photobooth")
    return render(request, "accounts/user_favorites.html", {"favorites": favorites})


@login_required
def toggle_favorite(request, photobooth_id):
    photobooth = get_object_or_404(Photobooth, id=photobooth_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, photobooth=photobooth)
    if not created:
        favorite.delete()  # si déjà en favoris => retirer
    return redirect(request.META.get("HTTP_REFERER", "user_dashboard"))


# Redirection

def home(request):
    return render(request, 'home.html')

def profile_view(request):
    return render(request, 'accounts/profile.html')

def redirect_to_password_reset(request):
    return redirect(reverse('password_reset_custom'))

def set_language_ajax(request):
    return HttpResponse("Set language AJAX endpoint")

def rgpd_delete_user(user):
    """Anonymiser un utilisateur pour le RGPD."""
    user.anonymize()

    for invoice in user.invoices.all():
        invoice.first_name = f"deleted_{user.id}"
        invoice.last_name = f"deleted_{user.id}"
        invoice.email = f"deleted_{user.id}@deleted.local"
        invoice.phone_number = None
        invoice.save()

    for reservation in user.reservations_linked.all():
        reservation.status = Reservation.CANCELED
        reservation.save()

@login_required
def delete_account(request):
    if request.method == "POST":
        # Anonymiser l'utilisateur
        rgpd_delete_user(request.user)
        logout(request)
        return redirect("account_deleted")

    return render(request, 'delete_account_confirmation.html')

@login_required
def generate_invoice(request, reservation_id):
    try:
        print("=== Début generate_invoice ===")
        print(f"Reservation ID reçu : {reservation_id}")

        reservation = get_object_or_404(Reservation, id=reservation_id)
        print(f"Réservation trouvée : {reservation} (user={reservation.user}, status={reservation.status})")

        # Vérification que l'utilisateur est soit le propriétaire de la réservation, soit un administrateur
        if reservation.user != request.user and not request.user.is_staff:
            print("Utilisateur non autorisé")
            return HttpResponse("Non autorisé", status=403)

        # Vérification que la réservation est confirmée
        if reservation.status != 'confirmed':
            print("Réservation non confirmée")
            return HttpResponse("La réservation doit être confirmée pour générer une facture.", status=400)

        # Si la facture n'existe pas encore, en créer une
        if not reservation.invoice:
            print("Pas de facture existante, création...")
            invoice = Invoice.objects.create(
                user=reservation.user,
                total_amount=reservation.photobooth.price,
            )
            reservation.invoice = invoice
            reservation.save()
            print(f"Facture créée : {invoice}")
        else:
            invoice = reservation.invoice
            print(f"Facture existante trouvée : {invoice}")

        # Appliquer un coupon si nécessaire
        if hasattr(reservation, 'coupon') and reservation.coupon:
            print(f"Coupon appliqué : {reservation.coupon}")
            invoice.apply_coupon(reservation.coupon)

        # Montants
        prix_initial = float(reservation.photobooth.price)
        prix_total = float(invoice.total_amount)
        discount = max(0.0, prix_initial - prix_total)

        # Création du PDF
        print("Initialisation du PDF...")
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Couleur et police par défaut
        p.setFillColor(colors.black)
        p.setStrokeColor(colors.black)

        # En-tête simple
        y = height - 50
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, y, "FACTURE DE RÉSERVATION")
        print("Titre écrit à y =", y)

        y -= 20
        p.setFont("Helvetica", 10)
        now = timezone.now()
        p.drawString(50, y, f"Date : {now.strftime('%d/%m/%Y %H:%M')}")
        p.drawRightString(width - 50, y, f"Facture n° {now.strftime('%Y%m%d%H%M%S')}-{reservation.id}")
        print("Date et numéro écrits à y =", y)

        # Ligne séparatrice
        y -= 15
        p.line(50, y, width - 50, y)

        # Infos société
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Émetteur :")
        p.setFont("Helvetica", 10)
        for line in [
            "Idealbooth SARL",
            "N° TVA : N TVA 12345678900978",
            "Tél : +32 465 45 67 89",
            "Email : bpgloire@gmail.com",
            "Adresse : 123 Rue des Lumières, 6000 Charleroi, Belgique"
        ]:
            y -= 15
            print("Écriture société à y =", y)
            p.drawString(60, y, line)

        # Infos client
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Destinataire :")
        p.setFont("Helvetica", 10)
        user_name = reservation.user.get_full_name() or reservation.user.username
        for line in [
            f"Nom : {user_name}",
            f"Email : {reservation.user.email or 'Non fourni'}",
            f"Tél : {getattr(reservation.user, 'phone_number', 'Non fourni')}",
            f"Adresse : {getattr(reservation.user, 'address', 'Non fournie')}"
        ]:
            y -= 15
            print("Écriture client à y =", y)
            p.drawString(60, y, line)

        # Détails de la réservation
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Détails de la réservation")
        p.setFont("Helvetica", 10)
        for line in [
            f"Photobooth : {reservation.photobooth.name}",
            f"Type d'événement : {reservation.event_type}",
            f"Date de début : {reservation.start_date.strftime('%d/%m/%Y')}",
            f"Date de fin : {reservation.end_date.strftime('%d/%m/%Y')}"
        ]:
            y -= 15
            print("Écriture réservation à y =", y)
            p.drawString(60, y, line)

        if hasattr(reservation, 'accessories') and reservation.accessories.exists():
            accessoires_list = ", ".join([acc.name for acc in reservation.accessories.all()])
            y -= 15
            print("Écriture accessoires à y =", y)
            p.drawString(60, y, f"Accessoires : {accessoires_list}")

        # Ligne séparatrice montants
        y -= 20
        p.line(50, y, width - 50, y)

        # Montants
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Montant")
        p.setFont("Helvetica", 10)
        y -= 15
        print("Écriture prix initial à y =", y)
        p.drawString(60, y, f"Prix initial : {prix_initial:.2f} €")

        if discount > 0 and prix_initial > 0:
            y -= 15
            print("Écriture réduction à y =", y)
            p.drawString(60, y, f"Réduction appliquée : {discount:.2f} € ({(discount/prix_initial)*100:.0f}%)")

        y -= 15
        print("Écriture prix total à y =", y)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, f"Prix TTC : {prix_total:.2f} €")

        # Remerciement simple
        y -= 30
        print("Écriture remerciement à y =", y)
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, y, "Merci pour votre confiance et votre réservation !")

        # Sauvegarde
        p.save()
        buffer.seek(0)
        print("PDF généré avec succès")
        return FileResponse(buffer, as_attachment=True, filename=f"facture_{reservation.id}.pdf")

    except Reservation.DoesNotExist:
        print("Réservation introuvable")
        return HttpResponse("Réservation introuvable.", status=404)
    except Exception as e:
        print("=== ERREUR ===")
        print(f"Erreur lors de la génération du PDF: {str(e)}")
        return HttpResponse(f"Une erreur est survenue : {str(e)}", status=500)
    

@login_required
def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html")


