from datetime import timedelta
from django.utils import timezone
from rest_framework.throttling import BaseThrottle

from .models import UserQuota, DiagramGenerationLog


# Default quota settings for users without a UserQuota record
DEFAULT_QUOTA_LIMIT = 10
DEFAULT_QUOTA_PERIOD = "day"


class DiagramGenerationThrottle(BaseThrottle):
    """
    Custom throttle for diagram generation endpoints.

    Checks user's quota from the UserQuota model and tracks usage
    via DiagramGenerationLog. Supports day/week/month periods.
    """

    def get_period_start(self, period: str) -> timezone.datetime:
        """Calculate the start of the current period."""
        now = timezone.now()
        if period == "day":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            # Start of the week (Monday)
            days_since_monday = now.weekday()
            start_of_week = now - timedelta(days=days_since_monday)
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return now

    def get_user_quota(self, user):
        """Get quota settings for a user, or return defaults."""
        try:
            return UserQuota.objects.get(user=user)
        except UserQuota.DoesNotExist:
            return None

    def get_usage_count(self, user, period_start) -> int:
        """Count diagram generations since period start."""
        return DiagramGenerationLog.objects.filter(
            user=user, created_at__gte=period_start
        ).count()

    def allow_request(self, request, view):
        """Check if the request should be allowed."""
        user = request.user

        if not user or not user.is_authenticated:
            return False

        quota = self.get_user_quota(user)

        # Use quota settings or defaults
        if quota:
            if quota.is_unlimited:
                return True
            quota_limit = quota.quota_limit
            period = quota.period
        else:
            quota_limit = DEFAULT_QUOTA_LIMIT
            period = DEFAULT_QUOTA_PERIOD

        period_start = self.get_period_start(period)
        usage_count = self.get_usage_count(user, period_start)

        if usage_count >= quota_limit:
            # Calculate wait time until next period
            self.wait_time = self._calculate_wait_time(period, period_start)
            return False

        return True

    def _calculate_wait_time(self, period: str, period_start) -> int:
        """Calculate seconds until the quota resets."""
        now = timezone.now()
        if period == "day":
            next_period = period_start + timedelta(days=1)
        elif period == "week":
            next_period = period_start + timedelta(weeks=1)
        elif period == "month":
            # Approximate: add 30 days
            next_period = period_start + timedelta(days=30)
        else:
            next_period = now + timedelta(days=1)

        return int((next_period - now).total_seconds())

    def wait(self):
        """Return the wait time until the quota resets."""
        return getattr(self, "wait_time", None)


def log_diagram_generation(user):
    """
    Log a diagram generation for rate limiting.
    Call this after successful diagram generation.
    """
    DiagramGenerationLog.objects.create(user=user)


def get_user_quota_status(user) -> dict:
    """
    Get the current quota status for a user.
    Useful for displaying remaining quota to users.
    """
    throttle = DiagramGenerationThrottle()
    quota = throttle.get_user_quota(user)

    if quota:
        if quota.is_unlimited:
            return {
                "limit": None,
                "used": 0,
                "remaining": None,
                "period": None,
                "is_unlimited": True,
            }
        quota_limit = quota.quota_limit
        period = quota.period
    else:
        quota_limit = DEFAULT_QUOTA_LIMIT
        period = DEFAULT_QUOTA_PERIOD

    period_start = throttle.get_period_start(period)
    usage_count = throttle.get_usage_count(user, period_start)

    return {
        "limit": quota_limit,
        "used": usage_count,
        "remaining": max(0, quota_limit - usage_count),
        "period": period,
        "is_unlimited": False,
    }
