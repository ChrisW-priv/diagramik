"""Fixtures specific to rate limiting tests."""

import pytest


@pytest.fixture
def user_with_quota_support(user):
    """Return a user that supports having a UserQuota created.

    This fixture ensures that any existing quota is cleared before returning the user.
    """
    # Delete any existing quota for this user (from previous tests)
    from quota_management.models import UserQuota

    UserQuota.objects.filter(user=user).delete()
    return user
