from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CookieConsentLog(models.Model):
    CHOICES = [
        ("all", "Tous les cookies"),
        ("essential", "Essentiels uniquement"),
        ("custom", "Personnalisé"),
    ]

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    choice = models.CharField(max_length=20, choices=CHOICES)
    analytics = models.BooleanField(default=False)
    marketing = models.BooleanField(default=False)
    personalization = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user or self.ip_address} - {self.choice} - {self.created_at}"
