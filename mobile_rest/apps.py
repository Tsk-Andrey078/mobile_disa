from django.apps import AppConfig


class MobileRestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mobile_rest'

    def ready(self):
        import mobile_rest.signals
