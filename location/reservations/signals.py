from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Reservation, Notification, Invoice

print(">>> signals.py loaded <<<")


@receiver(post_save, sender=Reservation)
def notify_user_on_confirmation(sender, instance, created, **kwargs):
    if instance.status == 'confirmed':
        if not Notification.objects.filter(
            user=instance.user,
            message__icontains=f"Votre réservation #{instance.id} a été confirmée"
        ).exists():
            Notification.objects.create(
                user=instance.user,
                message=f"Votre réservation #{instance.id} a été confirmée par l'administrateur."
            )

        if not instance.invoice:
            invoice = Invoice.objects.create(
                user=instance.user,
                total_amount=getattr(instance.photobooth, "price", 0),
                payment_status='pending'
            )
            Reservation.objects.filter(pk=instance.pk).update(invoice=invoice)


@receiver(post_save, sender=Invoice)
def update_payment_date(sender, instance, created, **kwargs):
    """
    Quand une facture est marquée comme 'paid' :
    - Met à jour la date de paiement si elle n'est pas encore définie
    """
    if instance.payment_status == 'paid' and not instance.payment_date:
        instance.payment_date = timezone.now()
        # Sauvegarde uniquement le champ payment_date pour éviter une boucle
        instance.save(update_fields=["payment_date"])
