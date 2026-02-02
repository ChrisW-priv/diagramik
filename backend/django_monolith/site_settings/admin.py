from django.contrib import admin
from .models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    fieldsets = (
        (
            "Default User Quotas",
            {
                "fields": ("quota_limit_default", "quota_period_default"),
                "description": "Default rate limits applied to newly registered users",
            },
        ),
        (
            "Email Rate Limiting",
            {
                "fields": ("email_rate_limit",),
                "description": "Maximum emails per hour for registration/password reset",
            },
        ),
    )
