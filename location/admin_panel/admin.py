from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse
from reservations.models import Reservation, Invoice
from .views import generate_invoice
from .models import Accessory, Message
from .models import Notification


# Gestion des factures
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('user__username', 'id')

admin.site.register(Accessory)

@admin.action(description="Marquer comme lu")
def mark_as_read(modeladmin, request, queryset):
    queryset.update(is_read=True)

@admin.action(description="Marquer comme non lu")
def mark_as_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('subject', 'body', 'sender__email', 'recipient__email')
    actions = [mark_as_read, mark_as_unread]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'photobooth',
        'title',
        'is_read',
        'created_at',
    )

    list_filter = (
        'is_read',
        'created_at',
    )

    search_fields = (
        'title',
        'message',
        'photobooth__name',
    )

    ordering = ('-created_at',)