# Commit historique : Mise en place des modèles (20 août 2025)
from django.db import models
from django.conf import settings
from photobooths.models import Photobooth


class Payment(models.Model):
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='admin_payments'  # <- important !
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user} - {self.amount}€ - {self.status}"

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_sent"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_received"
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.sender}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expiration_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    def is_expired(self):
        from django.utils import timezone
        return self.expiration_date < timezone.now().date()

class AdminNotification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    # optionnel si tu veux relier à un user
    user = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)

    def __str__(self):
        return self.message[:50]
    
class Accessory(models.Model):
    photobooth = models.ForeignKey(
        Photobooth,
        on_delete=models.CASCADE,
        related_name='admin_accessories'

    )
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='accessories/')

    def __str__(self):
        return self.name


