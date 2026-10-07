from django.test import TestCase
from django.utils import timezone
from accounts.models import CustomUser
from photobooths.models import Photobooth
from reservations.models import Reservation, Invoice, Notification


class ReservationSignalTests(TestCase):
    def setUp(self):
        # Crée un utilisateur et un photobooth de test
        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        self.booth = Photobooth.objects.create(
            name="Test Booth",
            price=100.00
        )

    def test_invoice_and_notification_created_on_confirmation(self):
        # Crée une réservation en attente
        reservation = Reservation.objects.create(
            user=self.user,
            photobooth=self.booth,
            start_date=timezone.now(),
            end_date=timezone.now(),
            status="pending"
        )

        # Confirme la réservation
        reservation.status = "confirmed"
        reservation.save()

        # Vérifie qu'une facture est créée
        self.assertIsNotNone(reservation.invoice)
        self.assertEqual(reservation.invoice.total_amount, self.booth.price)
        self.assertEqual(reservation.invoice.payment_status, "pending")

        # Vérifie qu'une notification est créée
        notif_exists = Notification.objects.filter(
            user=self.user,
            message__icontains=f"Votre réservation #{reservation.id} a été confirmée"
        ).exists()
        self.assertTrue(notif_exists)

    def test_payment_date_set_when_invoice_paid(self):
        # Crée une réservation confirmée
        reservation = Reservation.objects.create(
            user=self.user,
            photobooth=self.booth,
            start_date=timezone.now(),
            end_date=timezone.now(),
            status="confirmed"
        )

        invoice = reservation.invoice
        self.assertIsNotNone(invoice)

        # Marque la facture comme payée
        invoice.payment_status = "paid"
        invoice.save()

        # Vérifie que la date de paiement est définie
        self.assertIsNotNone(invoice.payment_date)
