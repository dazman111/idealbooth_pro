from django.utils import timezone
from .models import Reservation   # Import global propre


def is_photobooth_available(photobooth, start_date, end_date):
    """
    Vérifie si un photobooth est disponible entre deux dates (datetime).
    Retourne True s'il n'y a pas de réservation confirmée qui se chevauche.
    """

    overlapping = Reservation.objects.filter(
        photobooth=photobooth,
        status=Reservation.CONFIRMED,
        end_date__gte=start_date,
        start_date__lte=end_date
    )

    return not overlapping.exists()
