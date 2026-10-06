from rest_framework import serializers
from .models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = [
            'id',
            'user',
            'photobooth',
            'start_date',
            'end_date',
            'status',
            'date_location',
            'invoice'
        ]
        read_only_fields = ['invoice']  # Empêche modification directe

    def validate_status(self, value):
        """Valide que le statut est bien dans les choix autorisés."""
        valid_statuses = [choice[0] for choice in Reservation.STATUS_CHOICES]

        if value not in valid_statuses:
            raise serializers.ValidationError("Statut invalide")

        return value

    def update(self, instance, validated_data):
        """
        Override propre : si le statut change, on valide via validate_status().
        """
        if 'status' in validated_data:
            self.validate_status(validated_data['status'])

        return super().update(instance, validated_data)
