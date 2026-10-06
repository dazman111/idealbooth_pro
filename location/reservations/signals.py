from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Reservation, Notification, Invoice


@receiver(post_save, sender=Reservation)
def notify_user_on_confirmation(sender, instance, created, **kwargs):
    """
    Lorsqu'une réservation passe au statut CONFIRMED :
    - Crée une notification (si elle n'existe pas déjà)
    - Crée une facture (si elle n'existe pas déjà)
    """

    # On ne fait rien si la réservation n'est PAS confirmée
    if instance.status != Reservation.CONFIRMED:
        return

    # 🔔 1. Notification
    notif_message = f"Votre réservation #{instance.id} a été confirmée"

    if not Notification.objects.filter(
        user=instance.user,
        message__icontains=notif_message
    ).exists():
        Notification.objects.create(
            user=instance.user,
            message=f"{notif_message} par l'administrateur."
        )

    # 🧾 2. Facture
    if instance.invoice is None:
        invoice = Invoice.objects.create(
            user=instance.user,
            total_amount=getattr(instance.photobooth, "price", 0),
            payment_status=Invoice.PENDING
        )

        # IMPORTANT : update() pour éviter de relancer le signal
        Reservation.objects.filter(pk=instance.pk).update(invoice=invoice)


@receiver(post_save, sender=Invoice)
def update_payment_date(sender, instance, created, **kwargs):
    """
    Lorsqu'une facture passe au statut PAID :
    - Ajoute une date de paiement si elle n'existe pas encore
    """

    if instance.payment_status == Invoice.PAID and instance.payment_date is None:
        instance.payment_date = timezone.now()
        instance.save(update_fields=["payment_date"])
