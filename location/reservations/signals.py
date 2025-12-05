from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reservation, Notification

@receiver(post_save, sender=Reservation)
def notify_user_on_confirmation(sender, instance, created, **kwargs):
    if not created and instance.status == 'confirmed':
        # Vérifie si l'utilisateur n'a pas déjà reçu la notification pour éviter doublon
        if not Notification.objects.filter(user=instance.user, message__icontains=f"Votre réservation #{instance.id} a été confirmée").exists():
            Notification.objects.create(
                user=instance.user,
                message=f" Votre réservation #{instance.id} a été confirmée par l'administrateur."
            )