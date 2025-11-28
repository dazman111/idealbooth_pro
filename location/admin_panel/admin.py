from django.contrib import admin
from reservations.models import Reservation, Invoice


# --- Gestion des factures ---
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'created_at')
    search_fields = ('user__username', 'id')


# --- Gestion des réservations ---
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'photobooth', 'start_date', 'end_date', 'status', 'invoice')
    list_filter = ('status', 'start_date')
    actions = ['confirm_reservation', 'cancel_reservation']

    def confirm_reservation(self, request, queryset):
        pending_reservations = queryset.filter(status=Reservation.PENDING)
        count = pending_reservations.count()

        for reservation in pending_reservations:
            reservation.status = Reservation.CONFIRMED
            reservation.save()

        self.message_user(request, f"{count} réservation(s) confirmée(s).")

    confirm_reservation.short_description = "Confirmer la réservation sélectionnée (Paiement vérifié)"

    def cancel_reservation(self, request, queryset):
        pass  # Tu peux ajouter une logique ici si tu veux gérer les annulations
