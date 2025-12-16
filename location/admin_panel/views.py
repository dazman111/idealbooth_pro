from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.contrib import messages
from accounts.models import Message
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.utils import timezone
from io import BytesIO
from reservations.models import Reservation, Invoice
from .forms import PhotoboothForm
from photobooths.models import Photobooth
from .models import Payment
from datetime import datetime
import json
from django.conf import settings
import logging # Importer le module logging
from django.urls import reverse_lazy
from reportlab.lib import colors
from blog.models import Article
from .models import Coupon
from .forms import CouponForm
from reservations.models import Notification
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from coupons.models import Coupon, PromotionBanner
from .forms import CouponForm, PromotionBannerForm
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.contrib.auth import get_user_model
from django.contrib import messages
from photobooths.models import Accessory
from photobooths.forms import AccessoryForm
from .permissions import is_admin


# Configurez le logger pour cette application
logger = logging.getLogger(__name__) # 'admin_panel' par défaut si le nom de l'app est admin_panel

User = get_user_model()

def is_admin(user):
    print("is_admin check:", user.username, user.is_staff, user.is_superuser)
    return user.is_superuser or user.is_staff

class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return reverse_lazy('admin_panel:admin_dashboard')
        return reverse_lazy('accounts:user_dashboard')  # ou une autre vue utilisateur

@login_required
def admin_logout(request):
    logout(request)
    # Redirige vers une page spécifique admin après déconnexion
    return render(request, "admin_panel/logout.html", {"message": "Déconnexion admin réussie"})

#DASHBOARD ADMIN
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    # 🔢 Totaux
    total_users = User.objects.count()
    total_reservations = Reservation.objects.count()
    total_confirmed = Reservation.objects.filter(status=Reservation.CONFIRMED).count()
    total_cancelled = Reservation.objects.filter(status=Reservation.CANCELED).count()

    total_revenue = Reservation.objects.filter(
        status=Reservation.CONFIRMED
    ).aggregate(
        total=Sum('photobooth__price')
    )['total'] or 0

    # 📊 Réservations par mois
    reservations_by_month = (
        Reservation.objects
        .filter(status=Reservation.CONFIRMED)
        .annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    reservations_data = [
        {
            "month": item["month"].strftime("%Y-%m-01"),
            "count": item["count"]
        }
        for item in reservations_by_month
    ]

    # 💰 Revenus par mois
    revenue_by_month = (
        Reservation.objects
        .filter(status=Reservation.CONFIRMED)
        .annotate(month=TruncMonth('start_date'))
        .values('month')
        .annotate(total=Sum('photobooth__price'))
        .order_by('month')
    )

    revenue_data = [
        {
            "month": item["month"].strftime("%Y-%m-01"),
            "total": float(item["total"])
        }
        for item in revenue_by_month
    ]

    # 🔔 Notifications admin
    notifications = Notification.objects.filter(
        user__is_staff=True
    ).order_by('-created_at')

    unread_count = notifications.filter(read=False).count()

    context = {
        "total_users": total_users,
        "total_reservations": total_reservations,
        "total_confirmed": total_confirmed,
        "total_cancelled": total_cancelled,
        "total_revenue": total_revenue,
        "reservations_by_month": reservations_data,
        "revenue_by_month": revenue_data,
        "notifications": notifications,
        "unread_count": unread_count,
    }

    return render(request, "admin_panel/admin_dashboard.html", context)


#GESTION UTILISATEURS
@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.all().order_by('id')

    return render(request, 'admin_panel/manage_users.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user_detail = get_object_or_404(User, id=user_id)
    return render(request, 'admin_panel/partials/user_detail.html', {'user_detail': user_detail})

@login_required
@user_passes_test(is_admin)    
def edit_user(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        # On met à jour directement les champs
        user_obj.username = request.POST.get('username')
        user_obj.email = request.POST.get('email')
        user_obj.first_name = request.POST.get('first_name')
        user_obj.last_name = request.POST.get('last_name')
        user_obj.save()
        messages.success(request, "Utilisateur mis à jour avec succès.")

        # Renvoie le template directement pour avoir HTTP 200
        return render(
            request,
            'admin_panel/partials/edit_user.html',
            {
                'user': user_obj,
                'success': True  # pour ton template : afficher le bouton "Retour au dashboard"
            }
        )

    return render(
        request,
        'admin_panel/partials/edit_user.html',
        {'user': user_obj}
    )

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        # Désactivation
        user.is_active = False

        # Anonymisation
        user.first_name = ""
        user.last_name = ""
        user.email = f"deleted_{user.id}@example.com"
        user.username = f"deleted_{user.id}"

        # Marquer comme supprimé si champ ajouté
        if hasattr(user, "is_deleted"):
            user.is_deleted = True

        user.save()

        messages.success(request, "Utilisateur désactivé et anonymisé, transactions conservées.")
        return redirect("admin_panel:manage_users")

    return redirect("admin_panel:manage_users")


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_reactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.is_active = True
        user.save()
        messages.success(request, "Utilisateur réactivé avec succès.")
        return redirect("admin_panel:manage_users")
    return redirect("admin_panel:manage_users")


#GESTION PHOTOBOOTHS
@login_required
@user_passes_test(is_admin)
def manage_photobooths(request):
    photobooths = Photobooth.objects.all()
    return render(request, 'admin_panel/manage_photobooths.html', {'photobooths': photobooths})

@login_required
@user_passes_test(is_admin)
def photobooth_list(request):
    booths = Photobooth.objects.all()
    return render(request, "admin_panel/photobooths/manage_photobooths.html", {"booths": booths})

@login_required
@user_passes_test(is_admin)
def restock_photobooth(request, pk):
    booth = get_object_or_404(Photobooth, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "stock":
            booth.stock += 1
            booth.save()
            messages.success(request, "1 unité ajoutée au stock.")

        elif action == "online":
            if booth.stock > 0:
                booth.available += 1
                booth.stock -= 1
                booth.save()
                messages.success(request, "Un modèle du stock est repassé en ligne.")
            else:
                messages.error(request, "Aucun stock disponible pour remettre en ligne.")

        return redirect("admin_panel:admin_photobooth_list")

    return redirect("admin_panel:admin_photobooth_list")

@login_required
def rent_photobooth(request, pk):
    booth = get_object_or_404(Photobooth, pk=pk)

    if booth.available > 0:
        # Un booth en ligne est loué
        booth.available -= 1
        booth.save()
        messages.success(request, "Photobooth loué avec succès !")

        # Vérifie si on doit basculer du stock vers en ligne
        if booth.available == 0 and booth.stock > 0:
            booth.available += 1
            booth.stock -= 1
            booth.save()
            messages.info(request, "Un modèle du stock est repassé en ligne automatiquement.")
    else:
        messages.error(request, "Aucun photobooth disponible en ligne.")

    return redirect("photobooth_list")

@login_required
@user_passes_test(is_admin)
def add_photobooth(request):
    if request.method == 'POST':
        form = PhotoboothForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Photobooth ajouté avec succès.")
            return redirect('admin_panel:manage_photobooths')
        else:
            messages.error(request, "Erreur lors de l'ajout du photobooth. Veuillez vérifier les informations.")
    else:
        form = PhotoboothForm()
    return render(request, 'admin_panel/photobooth_form.html', {'form': form, 'title': 'Ajouter un photobooth'})

@login_required
@user_passes_test(is_admin)
def edit_photobooth(request, pk):
    booth = get_object_or_404(Photobooth, pk=pk)

    if request.method == 'POST':
        form = PhotoboothForm(request.POST, request.FILES, instance=booth)
        if form.is_valid():
            form.save()
            messages.success(request, "Photobooth modifié avec succès.")
            return redirect('admin_panel:manage_photobooths')  # ← redirection vers le dashboard
        else:
            messages.error(request, "Erreur lors de la modification du photobooth.")
    else:
        form = PhotoboothForm(instance=booth)

    return render(
        request,
        'admin_panel/photobooth_form.html',
        {
            'form': form,
            'title': 'Modifier le photobooth',
        }
    )


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_photobooth(request, pk):
    booth = get_object_or_404(Photobooth, pk=pk)
    booth.delete()
    messages.success(request, "Photobooth supprimé avec succès.")
    return redirect('photobooth_list')  #

@login_required
@user_passes_test(is_admin)
def manage_payments(request):
    payments = Payment.objects.all().order_by('-date') 
    
    # --- DÉBUT DES LIGNES DE DÉBOGAGE ---
    logger.debug("\n--- DÉBOGAGE PAIEMENTS ---")
    logger.debug(f"Nombre de paiements récupérés : {payments.count()}")
    if payments.exists():
        logger.debug("Détails des paiements :")
        for p in payments:
            logger.debug(f"  ID: {p.id}, Utilisateur: {p.user.username}, Montant: {p.amount}, Date: {p.date}, Statut: {p.status}, Méthode: {getattr(p, 'method', 'N/A')}, Facture URL: {getattr(p, 'invoice_url', 'N/A')}")
    else:
        logger.debug("Aucun paiement dans le queryset.")
    logger.debug("--- FIN DÉBOGAGE ---")

    context = {'payments': payments}
    return render(request, 'admin_panel/manage_payments.html', context)

#GESTION DES ACCESSOIRES
@login_required
@user_passes_test(is_admin)
def accessory_list(request):
    accessories = Accessory.objects.all()
    return render(request, "admin_panel/accessories/list.html", {"accessories": accessories})


@login_required
@user_passes_test(is_admin)
def add_accessory(request):
    if request.method == "POST":
        form = AccessoryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Accessoire ajouté avec succès.")
            return redirect("admin_panel:accessory_list")
    else:
        form = AccessoryForm()

    return render(request, "admin_panel/accessories/form.html", {"form": form, "title": "Ajouter un accessoire"})


@login_required
@user_passes_test(is_admin)
def edit_accessory(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk)

    if request.method == "POST":
        form = AccessoryForm(request.POST, request.FILES, instance=accessory)
        if form.is_valid():
            form.save()
            messages.success(request, "Accessoire modifié avec succès.")
            return redirect("admin_panel:accessory_list")
    else:
        form = AccessoryForm(instance=accessory)

    return render(request, "admin_panel/accessories/form.html", {"form": form, "title": "Modifier un accessoire"})


@login_required
@user_passes_test(is_admin)
def delete_accessory(request, pk):
    accessory = get_object_or_404(Accessory, pk=pk)
    accessory.delete()
    messages.success(request, "Accessoire supprimé.")
    return redirect("admin_panel:accessory_list")


@login_required
@user_passes_test(is_admin)
def manage_reservations(request):
    status = request.GET.get('status')
    user_id = request.GET.get('user')

    # IMPORTANT: Ajouter 'invoice' à select_related pour que les infos de facture soient disponibles dans le template
    reservations = Reservation.objects.select_related('user', 'photobooth', 'invoice').all()
    if status:
        reservations = reservations.filter(status=status)
    if user_id:
        reservations = reservations.filter(user__id=user_id)
    
    reservations = reservations.order_by('-start_date')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('admin_panel/partials/_reservation_table.html', {'reservations': reservations})
        return JsonResponse({'html': html})

    users = User.objects.all()
    return render(request, 'admin_panel/manage_reservations.html', {
        'reservations': reservations,
        'users': users
    })

@require_POST
@login_required
@user_passes_test(is_admin)
def update_reservation_status(request):
    logger.debug(f"Début de la fonction update_reservation_status. Méthode: {request.method}")
    try:
        data = json.loads(request.body)
        reservation_id = data.get('id')
        action = data.get('action')
        logger.debug(f"Requête reçue: ID={reservation_id}, Action={action}")

        if not reservation_id or not action:
            logger.warning(f"Données manquantes dans la requête: ID={reservation_id}, Action={action}. Corps reçu: {request.body.decode('utf-8')}")
            return JsonResponse({'success': False, 'error': "ID de réservation ou action manquant."}, status=400)

        reservation = get_object_or_404(Reservation.objects.select_related('invoice'), id=reservation_id)
        logger.debug(f"Réservation trouvée: ID={reservation.id}, Statut actuel={reservation.status}")

        message_success = ""
        error_message = ""

        if action == 'confirm':
            if reservation.status == 'pending':
                reservation.status = 'confirmed'
                reservation.save()
                message_success = "Réservation confirmée avec succès."
                logger.info(f"Réservation {reservation.id} confirmée.")
                envoyer_notification_email(
                    reservation.user,
                    'Votre réservation est confirmée',
                    f"Bonjour {reservation.user.username},\n\nVotre réservation du {reservation.start_date.strftime('%d/%m/%Y')} a bien été confirmée. Merci !"
                )
            else:
                error_message = "La réservation ne peut être confirmée que si son statut est 'En attente'."
                logger.warning(f"Tentative de confirmer la réservation {reservation.id} (statut actuel: {reservation.status}) qui n'est pas 'pending'.")
        elif action == 'cancel':
            # Assurez-vous que les constantes de statut sont correctement définies sur votre modèle Reservation.
            # Exemple: class Reservation(models.Model): PENDING='pending', CONFIRMED='confirmed', CANCELED='cancelled'
            if reservation.status in [Reservation.PENDING, Reservation.CONFIRMED]:
                reservation.status = Reservation.CANCELED
                reservation.save()
                message_success = "Réservation annulée avec succès."
                logger.info(f"Réservation {reservation.id} annulée.")
                envoyer_notification_email(
                    reservation.user,
                    'Votre réservation a été annulée',
                    f"Bonjour {reservation.user.username},\n\nNous vous informons que votre réservation du {reservation.start_date.strftime('%d/%m/%Y')} a été annulée."
                )
            else:
                error_message = "La réservation ne peut être annulée que si son statut est 'En attente' ou 'Confirmée'."
                logger.warning(f"Tentative d'annuler la réservation {reservation.id} (statut actuel: {reservation.status}) qui n'est ni 'pending' ni 'confirmed'.")
        elif action == 'mark_paid':
            if reservation.invoice:
                if reservation.invoice.payment_status != 'paid':
                    reservation.invoice.payment_status = 'paid'
                    reservation.invoice.save()
                    # Si la réservation est en attente, la confirmer aussi quand elle est marquée comme payée
                    if reservation.status == Reservation.PENDING:
                        reservation.status = Reservation.CONFIRMED
                        reservation.save()
                    message_success = "La réservation et la facture associée ont été marquées comme payées."
                    logger.info(f"Réservation {reservation.id} et facture {reservation.invoice.id} marquées comme payées.")
                    envoyer_notification_email(
                        reservation.user,
                        'Votre réservation a été marquée comme payée',
                        f"Bonjour {reservation.user.username},\n\nVotre réservation du {reservation.start_date.strftime('%d/%m/%Y')} a été marquée comme payée."
                    )
                else:
                    error_message = "La facture de cette réservation est déjà marquée comme payée."
                    logger.warning(f"Tentative de marquer la facture {reservation.invoice.id} de la réservation {reservation.id} comme payée, mais elle l'est déjà.")
            else:
                error_message = "Aucune facture associée à cette réservation pour marquer comme payée."
                logger.warning(f"Tentative de marquer la réservation {reservation.id} comme payée, mais aucune facture associée.")
        else:
            error_message = "Action invalide spécifiée."
            logger.warning(f"Action '{action}' invalide reçue pour la réservation {reservation.id}.")

        if error_message:
            logger.error(f"Erreur logique dans update_reservation_status pour ID={reservation_id}, Action={action}: {error_message}")
            return JsonResponse({'success': False, 'error': error_message}, status=400)

        # Récupérer les réservations à nouveau pour rafraîchir le tableau après la mise à jour
        status_filter_param = request.GET.get('status')
        user_id_filter_param = request.GET.get('user')
        
        reservations = Reservation.objects.select_related('user', 'photobooth', 'invoice').all() 
        if status_filter_param:
            reservations = reservations.filter(status=status_filter_param)
        if user_id_filter_param:
            reservations = reservations.filter(user__id=user_id_filter_param)
        
        reservations = reservations.order_by('-start_date')

        html = render_to_string('admin_panel/partials/_reservation_table.html', {'reservations': reservations})
        logger.info(f"Action {action} réussie pour réservation {reservation.id}. Renvoyé HTML mis à jour.")
        return JsonResponse({'success': True, 'html': html, 'message': message_success})

    except Reservation.DoesNotExist:
        logger.error(f"Reservation.DoesNotExist pour l'ID de réservation {reservation_id} fourni.")
        return JsonResponse({'success': False, 'error': 'Réservation introuvable.'}, status=404)
    except json.JSONDecodeError:
        logger.error(f"JSONDecodeError: Requête invalide (JSON mal formé). Corps: {request.body.decode('utf-8')}")
        return JsonResponse({'success': False, 'error': "Requête invalide : JSON mal formé."}, status=400)
    except Exception as e:
        logger.exception(f"Une erreur inattendue est survenue dans update_reservation_status pour ID={reservation_id}, Action={action}.")
        return JsonResponse({'success': False, 'error': f'Une erreur inattendue est survenue : {str(e)}'}, status=500)

@login_required
@user_passes_test(is_admin)
def manage_reservations(request):
    status = request.GET.get('status')
    user_id = request.GET.get('user')

    reservations = Reservation.objects.select_related('user', 'photobooth', 'invoice').all()
    if status:
        reservations = reservations.filter(status=status)
    if user_id:
        reservations = reservations.filter(user__id=user_id)
    
    reservations = reservations.order_by('-start_date')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('admin_panel/partials/_reservation_table.html', {'reservations': reservations})
        return JsonResponse({'html': html})

    users = User.objects.all()
    return render(request, 'admin_panel/manage_reservations.html', {
        'reservations': reservations,
        'users': users
    })


@login_required
def reservation_detail(request, reservation_id):
    try:
        reservation = Reservation.objects.select_related('user', 'photobooth').get(id=reservation_id)
        if not request.user.is_staff and not request.user.is_superuser and reservation.user != request.user:
            return JsonResponse({'success': False, 'error': 'Non autorisé à voir les détails de cette réservation.'}, status=403)

        html = render_to_string(
            'admin_panel/partials/_reservation_detail.html',
            {'reservation': reservation},
            request=request   # ← important
        )

        return JsonResponse({'success': True, 'html': html})
    except Reservation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Réservation non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Une erreur inattendue est survenue : {str(e)}'}, status=500)

# Configuration de La facture

@login_required
@user_passes_test(is_admin)
def admin_facture_detail(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)

    # Vérification que l'utilisateur connecté est soit l'utilisateur de la réservation, soit un administrateur
    if reservation.user != request.user and not request.user.is_staff:
        return HttpResponse("Non autorisé", status=403)

    # On suppose que chaque réservation confirmée a une facture liée
    invoice = reservation.invoice
    return render(request, "admin_panel/facture_detail.html", {
        "reservation": reservation,
        "invoice": invoice,
    })


@login_required
def generate_invoice(request, reservation_id):
    try:
        reservation = get_object_or_404(Reservation, id=reservation_id)

        # Autorisation
        if reservation.user != request.user and not request.user.is_staff:
            return HttpResponse("Non autorisé", status=403)

        # Statut confirmé obligatoire
        if reservation.status != 'confirmed':
            return HttpResponse("La réservation doit être confirmée pour générer une facture.", status=400)

        # Créer la facture si absente
        if not reservation.invoice:
            invoice = Invoice.objects.create(
                user=reservation.user,
                total_amount=reservation.photobooth.price,
            )
            reservation.invoice = invoice
            reservation.save()
        else:
            invoice = reservation.invoice

        # Appliquer un coupon si présent
        if hasattr(reservation, 'coupon') and reservation.coupon:
            invoice.apply_coupon(reservation.coupon)

        # Montants (convertis en float pour formatage)
        prix_initial = float(reservation.photobooth.price)
        prix_total = float(invoice.total_amount)
        discount = max(0.0, prix_initial - prix_total)

        # PDF
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
        y -= 20
        p.setFont("Helvetica", 10)
        now = timezone.now()
        p.drawString(50, y, f"Date : {now.strftime('%d/%m/%Y %H:%M')}")
        p.drawRightString(width - 50, y, f"Facture n° {now.strftime('%Y%m%d%H%M%S')}-{reservation.id}")

        # Ligne séparatrice
        y -= 15
        p.line(50, y, width - 50, y)

        # Infos société
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Émetteur :")
        p.setFont("Helvetica", 10)
        y -= 15; p.drawString(60, y, "Idealbooth SARL")
        y -= 15; p.drawString(60, y, "N° TVA : N TVA 12345678900978")
        y -= 15; p.drawString(60, y, "Tél : +32 465 45 67 89")
        y -= 15; p.drawString(60, y, "Email : bpgloire@gmail.com")
        y -= 15; p.drawString(60, y, "Adresse : 123 Rue des Lumières, 6000 Charleroi, Belgique")

        # Infos client
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Destinataire :")
        p.setFont("Helvetica", 10)
        user_name = reservation.user.get_full_name() or reservation.user.username
        y -= 15; p.drawString(60, y, f"Nom : {user_name}")
        y -= 15; p.drawString(60, y, f"Email : {reservation.user.email or 'Non fourni'}")
        y -= 15; p.drawString(60, y, f"Tél : {getattr(reservation.user, 'phone_number', 'Non fourni')}")
        y -= 15; p.drawString(60, y, f"Adresse : {getattr(reservation.user, 'address', 'Non fournie')}")

        # Détails de la réservation
        y -= 25
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Détails de la réservation")
        p.setFont("Helvetica", 10)
        y -= 15; p.drawString(60, y, f"Photobooth : {reservation.photobooth.name}")
        y -= 15; p.drawString(60, y, f"Type d'événement : {reservation.event_type}")
        y -= 15; p.drawString(60, y, f"Date de début : {reservation.start_date.strftime('%d/%m/%Y')}")
        y -= 15; p.drawString(60, y, f"Date de fin : {reservation.end_date.strftime('%d/%m/%Y')}")

        if hasattr(reservation, 'accessories') and reservation.accessories.exists():
            accessoires_list = ", ".join([acc.name for acc in reservation.accessories.all()])
            y -= 15; p.drawString(60, y, f"Accessoires : {accessoires_list}")

        # Ligne séparatrice montants
        y -= 20
        p.line(50, y, width - 50, y)

        # Montants
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Montant")
        p.setFont("Helvetica", 10)
        y -= 15; p.drawString(60, y, f"Prix initial : {prix_initial:.2f} €")
        if discount > 0 and prix_initial > 0:
            y -= 15; p.drawString(60, y, f"Réduction appliquée : {discount:.2f} € ({(discount/prix_initial)*100:.0f}%)")
        y -= 15; p.setFont("Helvetica-Bold", 11); p.drawString(60, y, f"Prix TTC : {prix_total:.2f} €")

        # Remerciement simple
        y -= 30
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, y, "Merci pour votre confiance et votre réservation !")

        # Sauvegarde (une seule page, pas de showPage)
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"facture_{reservation.id}.pdf")

    except Reservation.DoesNotExist:
        return HttpResponse("Réservation introuvable.", status=404)
    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {str(e)}")
        return HttpResponse(f"Une erreur est survenue : {str(e)}", status=500)

def envoyer_notification_email(user, sujet, message):
    try:
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email à {user.email}: {e}")

def manage_blog(request):
    # On récupère uniquement les articles publiés (pas les brouillons)
    articles = Article.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/manage_blog.html', {'articles': articles})


def cancelled_count_api(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        count = Reservation.objects.filter(status="canceled").count()
        return JsonResponse({"cancelled_count": count})
    return JsonResponse({"error": "Invalid request"}, status=400)


@staff_member_required 
def admin_messages(request):
    # Tous les messages reçus par l'admin
    messages_list = Message.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = messages_list.filter(is_read=False).count()

    # voici la réponse
    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        body = request.POST.get('body')
        parent_msg = get_object_or_404(Message, id=parent_id)
        Message.objects.create(
            sender=request.user,
            recipient=parent_msg.sender,
            subject=f"Re: {parent_msg.subject}",
            body=body,
            parent=parent_msg
        )
        parent_msg.is_read = True
        parent_msg.save()
        messages.success(request, "Réponse envoyée avec succès.")
        return redirect('admin_panel:admin_messages')

    return render(request, 'admin_panel/messages.html', {
        'messages_list': messages_list,
        'unread_count': unread_count
    })

#LISTE COUPONS
@login_required
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, "admin_panel/coupons/manage_coupons.html", {"coupons": coupons})

# Ajouter un coupon
@login_required
def add_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon ajouté avec succès.")
            return redirect("coupon_list")
    else:
        form = CouponForm()
    return render(request, "admin_panel/coupons/add_coupon.html", {"form": form})

# Modifier un coupon
@login_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == "POST":
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            messages.success(request, "Coupon modifié avec succès.")
            return redirect("admin_panel:admin_coupon_list")

    else:
        form = CouponForm(instance=coupon)
    return render(request, "admin_panel/coupons/edit_coupon.html", {"form": form, "coupon": coupon})

# Supprimer un coupon
@login_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, "Coupon supprimé.")
    return redirect("admin_panel:admin_coupon_list")
