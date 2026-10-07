from django.apps import AppConfig

class ReservationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reservations'

    def ready(self):
        # Import des signaux pour qu'ils soient enregistrés au démarrage
        import reservations.signals
