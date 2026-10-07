from django.contrib import admin
from .models import CookieConsentLog

@admin.register(CookieConsentLog)
class CookieConsentLogAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "choice", "analytics", "marketing", "personalization", "created_at")
    list_filter = ("choice", "analytics", "marketing", "personalization", "created_at")
    search_fields = ("user__username", "ip_address", "user_agent")
