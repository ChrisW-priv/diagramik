from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserQuota
from site_settings.models import SiteSettings

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_quota(sender, instance, created, **kwargs):
    """Create UserQuota with default values from SiteSettings when User is created."""
    if created:
        site_settings = SiteSettings.load()
        UserQuota.objects.create(
            user=instance,
            quota_limit=site_settings.quota_limit_default,
            period=site_settings.quota_period_default,
        )
