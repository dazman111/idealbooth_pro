# Commit historique : Mise en place des modèles (20 août 2025)
from django.db import models
from django.conf import settings
from photobooths.models import Photobooth
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = settings.AUTH_USER_MODEL



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
    CATEGORY_CHOICES = [
        ('fond_ecran', 'Fond d\'écran'),
        ('accessoire', 'Accessoire'),
    ]

    photobooth = models.ForeignKey(Photobooth, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="accessories/", null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='accessoire')

    def __str__(self):
        return self.name
    

class Devis(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
    )

    # L’entreprise = un utilisateur avec account_type="company"
    entreprise = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devis_entreprise"
    )

    # Le client = un utilisateur normal
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devis_client"
    )

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="devis_admin"
    )

    numero = models.CharField(max_length=50, unique=True)
    date_creation = models.DateTimeField(default=timezone.now)

    description = models.TextField(default="Prestation Photobooth")
    duree = models.PositiveIntegerField(default=2)

    prix_ht = models.DecimalField(max_digits=10, decimal_places=2)
    tva = models.DecimalField(max_digits=10, decimal_places=2, default=21)
    prix_ttc = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Devis {self.numero} - {self.client.username}"
    
    
class PromotionBanner(models.Model):
    message = models.CharField(max_length=255)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

class Notification(models.Model):
    photobooth = models.ForeignKey(Photobooth, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)