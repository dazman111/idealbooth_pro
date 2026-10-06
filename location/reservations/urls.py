from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ReservationViewSet,
    invoice_pdf,
    stripe_webhook,
    cancel_reservation,
    UserReservationsView,
)

# Router API REST
router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    # API REST (ViewSet)
    path('', include(router.urls)),

    # API : réservations de l'utilisateur connecté
    path('users/reservations/', UserReservationsView.as_view(), name='user_reservations'),

    # Facture PDF
    path('facture/<int:invoice_id>/', invoice_pdf, name='invoice_pdf'),

    # Stripe Webhook
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),

    # Annulation d'une réservation (HTML)
    path('cancel/<int:reservation_id>/', cancel_reservation, name='cancel_reservation'),
]
