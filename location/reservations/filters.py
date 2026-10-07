import django_filters
from .models import Reservation


class ReservationFilter(django_filters.FilterSet):
    start_date = django_filters.DateTimeFilter(
        field_name="start_date",
        lookup_expr='gte',
        label="À partir du"
    )

    end_date = django_filters.DateTimeFilter(
        field_name="end_date",
        lookup_expr='lte',
        label="Jusqu'au"
    )

    status = django_filters.ChoiceFilter(
        field_name="status",
        choices=Reservation.STATUS_CHOICES,
        label="Statut"
    )

    photobooth = django_filters.NumberFilter(
        field_name="photobooth",
        lookup_expr='exact',
        label="Photobooth ID"
    )

    class Meta:
        model = Reservation
        fields = ['start_date', 'end_date', 'status', 'photobooth']
