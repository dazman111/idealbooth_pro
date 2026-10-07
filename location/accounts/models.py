from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class CustomUser(AbstractUser):
    # Types de compte
    ACCOUNT_TYPES = (
        ('user', 'Particulier'),
        ('company', 'Entreprise'),
    )

    # Champs supplémentaires
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default='user'
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    heure_livraison = models.TimeField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    # Champs spécifiques entreprise (utilisés si account_type == "company")
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_vat_number = models.CharField(max_length=50, blank=True, null=True)
    company_address = models.CharField(max_length=255, blank=True, null=True)

    # Gestion de suppression programmée
    deleted_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_deleted(self):
        """Retourne True si l'utilisateur est déjà supprimé/anonymisé."""
        return self.deleted_at is not None and self.deleted_at <= timezone.now()

    @property
    def is_pending_deletion(self):
        """Retourne True si la suppression est programmée mais pas encore exécutée."""
        return self.deleted_at is not None and self.deleted_at > timezone.now()

    def schedule_deletion(self):
        """Programme la suppression dans 30 jours."""
        self.deleted_at = timezone.now() + timedelta(days=30)
        self.is_active = False
        self.save()

    def anonymize(self):
        """Suppression RGPD immédiate : anonymisation totale."""
        self.username = f"deleted_user_{self.id}"
        self.email = f"deleted_{self.id}@deleted.local"
        self.first_name = ""
        self.last_name = ""
        self.phone_number = None
        self.address = None
        self.profile_picture = None

        # On anonymise aussi les infos entreprise
        self.company_name = None
        self.company_vat_number = None
        self.company_address = None

        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def cancel_deletion(self):
        """Annule la suppression programmée."""
        self.deleted_at = None
        self.is_active = True
        self.save()

    def save(self, *args, **kwargs):
        """Sécurité : empêcher le changement de type de compte."""
        if self.pk:  # modification
            old = CustomUser.objects.get(pk=self.pk)
            if old.account_type != self.account_type:
                self.account_type = old.account_type
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.user.username} - {self.created_at}"


class Devis(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('refused', 'Refusé'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devis"
    )

    reservation = models.ForeignKey(
        'reservations.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devis_set'
    )

    numero = models.CharField(max_length=50, unique=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # Informations entreprise
    company_name = models.CharField(max_length=255)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    company_phone = models.CharField(max_length=50, blank=True, null=True)
    company_email = models.EmailField(blank=True, null=True)
    company_bce = models.CharField(max_length=50, blank=True, null=True)
    company_vat_number = models.CharField(max_length=50, blank=True, null=True)

    # Info client entreprise
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_address = models.CharField(max_length=255, blank=True, null=True)
    client_vat_number = models.CharField(max_length=50, blank=True, null=True)

    # Informations Photobooth
    description = models.TextField(default="Prestation Photobooth")
    duree = models.PositiveIntegerField(default=1)  # en jours
    prix_ht = models.DecimalField(max_digits=10, decimal_places=2)
    tva = models.DecimalField(max_digits=10, decimal_places=2, default=21)
    prix_ttc = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Devis {self.numero} - {self.user.username}"
    
class Facture(models.Model):
    devis = models.OneToOneField(
        Devis,
        on_delete=models.CASCADE,
        related_name="facture"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="factures"
    )

    numero = models.CharField(max_length=50, unique=True)
    date_creation = models.DateTimeField(default=timezone.now)

    # Copie des infos du devis
    description = models.TextField()
    duree = models.PositiveIntegerField()
    montant_ht = models.DecimalField(max_digits=10, decimal_places=2)
    tva = models.DecimalField(max_digits=10, decimal_places=2)
    montant_ttc = models.DecimalField(max_digits=10, decimal_places=2)

    # Infos entreprise
    company_name = models.CharField(max_length=255)
    company_address = models.CharField(max_length=255, blank=True, null=True)
    company_vat_number = models.CharField(max_length=50, blank=True, null=True)

    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Non payée'),
        ('paid', 'Payée'),
    ], default='unpaid')

    def __str__(self):
        return f"Facture {self.numero} - {self.user.username}"

class InternalMessage(models.Model):
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} ({self.sender} → {self.recipient})"
