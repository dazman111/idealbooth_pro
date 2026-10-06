from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'photobooth',
        'start_date',
        'end_date',
        'status',
        'event_type',
        'invoice',
    )

    list_filter = (
        'status',
        'event_type',
        'photobooth',
        'start_date',
    )

    search_fields = (
        'user__email',
        'user__username',
        'photobooth__name',
    )

    autocomplete_fields = (
        'user',
        'photobooth',
        'invoice',
    )

    ordering = ('-start_date',)

    readonly_fields = ('created_at',)

    fieldsets = (
        ("Informations générales", {
            "fields": (
                'user',
                'photobooth',
                'status',
                'event_type',
                'quantity',
            )
        }),
        ("Dates", {
            "fields": (
                'start_date',
                'end_date',
                'date_location',
            )
        }),
        ("Accessoires", {
            "fields": ('accessories',),
        }),
        ("Facturation", {
            "fields": ('invoice',),
        }),
        ("Métadonnées", {
            "fields": ('created_at',),
        }),
    )

