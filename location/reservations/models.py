from django.db import models
from django.conf import settings
from coupons.models import Coupon
from datetime import date
from django.utils.translation import gettext_lazy as _
from django.utils import timezone  # Ajout nécessaire pour timezone.now()
from accounts.models import CustomUser


class Reservation(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'
    
    STATUS_CHOICES = [
        (PENDING, _('En attente')),
        (CONFIRMED, _('Confirmée')),
        (CANCELED, _('Annulée')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photobooth = models.ForeignKey('photobooths.Photobooth', on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    date_location = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    quantity = models.PositiveIntegerField(default=2)

    invoice = models.ForeignKey(
        'Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations_linked'
    )
    # --- Nouveaux champs ---
    MARIAGE = 'mariage'
    BAPTEME = 'bapteme'
    ANNIVERSAIRE = 'anniversaire'
    ENTREPRISE = 'entreprise'

    EVENT_CHOICES = [
        (MARIAGE, 'Mariage'),
        (BAPTEME, 'Baptême'),
        (ANNIVERSAIRE, 'Anniversaire'),
        (ENTREPRISE, 'Entreprise'),
    ]

    event_type = models.CharField(
        max_length=20,
        choices=EVENT_CHOICES,
        default=MARIAGE,
        verbose_name="Type d'événement"
    )

    accessories = models.ManyToManyField(
        'photobooths.Accessory',  # Assure-toi d’avoir un modèle Accessory dans photobooths
        blank=True,
        related_name='reservations'
    )

    def __str__(self):
        return f"{self.photobooth.name} - {self.status} ({self.start_date.date()} → {self.end_date.date()})"

    def is_available(self):
        from .utils import is_photobooth_available
        return is_photobooth_available(self.photobooth, self.start_date, self.end_date)
    
    def est_active(self):
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin and not self.retourne

    @classmethod
    def check_availability(cls, photobooth, start_date, end_date):
        from .utils import is_photobooth_available
        return is_photobooth_available(photobooth, start_date, end_date)

    # --- Ajout des méthodes save et delete pour mise à jour du stock ---
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.photobooth.update_available()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.photobooth.update_available()

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente de paiement')),
        ('paid', _('Payée')),
        ('failed', _('Échec du paiement')),
        ('refunded', _('Remboursée')),
        ('cancelled', _('Annulée par l\'utilisateur')),
    ]

    # Lien direct vers accounts.CustomUser
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,related_name="invoices")

    # Champs copiés depuis CustomUser
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    stripe_paid = models.BooleanField(default=False)


    payment_date = models.DateTimeField(null=True, blank=True)

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Montant total de la facture (incluant les réductions).")
    )
    payment_status = models.CharField(
        max_length=50,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    stripe_checkout_session_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text=_("ID de la session Stripe Checkout.")
    )
    stripe_payment_intent_id = models.CharField(
        max_length=255, null=True, blank=True, unique=True,
        help_text=_("ID du Payment Intent Stripe après succès.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Coupon information
    coupon_used = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Coupon appliqué à cette facture."
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant de la réduction appliquée."
    )

    def save(self, *args, **kwargs):
        # Copie les infos de l’utilisateur au moment de la sauvegarde
        if self.user:
            self.first_name = self.user.first_name
            self.last_name = self.user.last_name
            self.email = self.user.email
            self.address = self.user.address
            self.phone_number = self.user.phone_number
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Facture #{self.id} - {self.total_amount}€ "
            f"({self.get_payment_status_display()}) - "
            f"{self.first_name} {self.last_name} ({self.email})"
        )

    def apply_coupon(self, coupon: Coupon):
        """Applique un coupon à la facture et met à jour le montant final."""
        if coupon and coupon.est_valide():
            remise = coupon.apply_discount(self.total_amount)
            self.discount_amount = remise
            self.coupon_used = coupon
            self.total_amount -= max(self.total_amount - remise, 0)
            self.save()
            return True
        return False
    

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification pour {self.user.username} - {self.message[:20]}"
