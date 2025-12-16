from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    is_deleted = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/',blank=True,null=True)

    # RGPD
    deleted_at = models.DateTimeField(null=True, blank=True)

    def is_deleted(self):
        return self.deleted_at is not None and self.deleted_at <= timezone.now()

    @property
    def is_pending_deletion(self):
        return self.deleted_at is not None and self.deleted_at > timezone.now()

    def schedule_deletion(self):
        """Programme la suppression dans 30 jours"""
        self.deleted_at = timezone.now() + timedelta(days=30)
        self.is_active = False
        self.save()

    def anonymize(self):
        """Suppression RGPD immédiate"""
        self.username = f"deleted_user_{self.id}"
        self.email = f"deleted_{self.id}@deleted.local"
        self.first_name = ""
        self.last_name = ""
        self.phone_number = None
        self.address = None
        self.profile_picture = None
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def cancel_deletion(self):
        """Annule la suppression programmée"""
        self.deleted_at = None
        self.is_active = True
        self.save()

    def __str__(self):
        return self.username


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
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.sender}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification pour {self.user.username} - {self.created_at}"
