from django.apps import AppConfig


class QuotaManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "quota_management"
    verbose_name = "Quota Management"

    def ready(self):
        import quota_management.signals  # noqa
