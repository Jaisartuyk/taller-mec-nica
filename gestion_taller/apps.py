from django.apps import AppConfig


class GestionTallerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_taller'

    def ready(self):
        import gestion_taller.signals
