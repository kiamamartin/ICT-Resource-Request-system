from django.apps import AppConfig


class ResourceRequestsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "resource_requests"
    
    def ready(self):
        import resource_requests.signals