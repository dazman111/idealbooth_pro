from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'photobooth', 'start_date', 'status')
    list_filter = ('status', 'event_type', 'photobooth')
    search_fields = ('user__email', 'photobooth__name')
    autocomplete_fields = ('user', 'photobooth', 'invoice', 'accessories')
