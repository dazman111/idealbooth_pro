from django.utils import timezone


def is_photobooth_available(photobooth, start_date, end_date):
    """
    Vérifie si un photobooth est disponible entre deux dates (datetime).
    Retourne True s'il n'y a pas de réservation confirmée qui se chevauche.
    """
    from .models import Reservation  # Import local pour éviter l'import circulaire

    overlapping = Reservation.objects.filter(
        photobooth=photobooth,
        status=Reservation.CONFIRMED,
        end_date__gte=start_date,
        start_date__lte=end_date
    )
    return not overlapping.exists()

# accounts/utils.py
def rgpd_delete_user(user):
    """Anonymiser un utilisateur pour le RGPD."""
    # Anonymiser les informations personnelles
    user.anonymize()

    # S'assurer que les factures restent attachées à l'utilisateur, mais que ses informations sont anonymisées
    for invoice in user.invoices.all():  # Assurez-vous de bien avoir ce `related_name="invoices"` dans Invoice
        invoice.first_name = f"deleted_{user.id}"
        invoice.last_name = f"deleted_{user.id}"
        invoice.email = f"deleted_{user.id}@deleted.local"
        invoice.phone_number = None
        invoice.save()

    # Optionnel : marquer les réservations ou autres objets liés pour qu'ils ne soient plus actifs
    for reservation in user.reservations_linked.all():
        reservation.status = Reservation.CANCELED  # On annule la réservation si nécessaire
        reservation.save()

