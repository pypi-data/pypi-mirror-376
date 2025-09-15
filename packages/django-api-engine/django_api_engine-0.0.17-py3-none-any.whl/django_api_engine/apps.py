from django.apps import AppConfig


class DjangoApiEngineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_api_engine"

    def ready(self):
        super().ready()
        import models
        import signals
        import tasks
