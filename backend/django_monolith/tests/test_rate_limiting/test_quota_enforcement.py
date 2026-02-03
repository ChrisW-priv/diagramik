"""Tests for quota enforcement and rate limiting."""

import pytest
from rest_framework import status
from freezegun import freeze_time
from tests.factories import DiagramGenerationLogFactory
from quota_management.models import DiagramGenerationLog
from site_settings.models import SiteSettings

pytestmark = pytest.mark.django_db


class TestQuotaEnforcement:
    """Tests for quota enforcement."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def site_settings(self):
        """Create or get site settings with default quota."""
        settings, _ = SiteSettings.objects.get_or_create(
            id=1, defaults={"quota_limit_default": 10}
        )
        return settings

    @freeze_time("2026-01-01 12:00:00")
    def test_default_quota_limits_after_10_requests(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that default quota limits user after configured requests."""
        # Arrange - make 10 requests (default limit)
        for i in range(10):
            DiagramGenerationLogFactory(user=user)

        # Act - 11th request should be throttled
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @freeze_time("2026-01-01 12:00:00")
    def test_custom_quota_overrides_default(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that custom user quota overrides site default."""
        # Arrange - set custom quota to 5
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=5, period="day")
        )

        # Make 5 requests
        for i in range(5):
            DiagramGenerationLogFactory(user=user)

        # Act - 6th request should be throttled
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @freeze_time("2026-01-01 12:00:00")
    def test_unlimited_quota_allows_infinite_requests(
        self, authenticated_client, diagrams_url, mock_agent_call, user
    ):
        """Test that unlimited quota allows unlimited requests."""
        # Arrange - set unlimited quota
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(user=user, defaults=dict(is_unlimited=True))

        # Make 100 requests (way over normal limit)
        for i in range(100):
            DiagramGenerationLogFactory(user=user)

        # Act - should still succeed
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    @freeze_time("2026-01-01 12:00:00")
    def test_quota_returns_429_with_detail(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that quota enforcement returns proper 429 response."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="day")
        )

        # Make 3 requests
        for i in range(3):
            DiagramGenerationLogFactory(user=user)

        # Act
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "detail" in response.data

    @freeze_time("2026-01-01 12:00:00")
    def test_quota_logs_successful_generations(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that successful diagram generation is logged."""
        # Arrange
        initial_count = DiagramGenerationLog.objects.filter(user=user).count()

        # Act
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            DiagramGenerationLog.objects.filter(user=user).count() == initial_count + 1
        )

    @freeze_time("2026-01-01 12:00:00")
    def test_quota_does_not_log_throttled_requests(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that throttled requests are not logged."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="day")
        )

        # Make 2 requests
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        initial_count = DiagramGenerationLog.objects.filter(user=user).count()

        # Act - this should be throttled
        response = authenticated_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        # Count should not increase
        assert DiagramGenerationLog.objects.filter(user=user).count() == initial_count

    @freeze_time("2026-01-01 12:00:00")
    def test_quota_does_not_affect_get_requests(
        self, authenticated_client, diagrams_url, user, site_settings
    ):
        """Test that quota only applies to POST requests, not GET."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="day")
        )

        # Make 2 POST requests
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        # Act - GET request should still work
        response = authenticated_client.get(diagrams_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

    @freeze_time("2026-01-01 12:00:00")
    def test_different_users_have_separate_quotas(
        self, api_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that different users have independent quota limits."""
        # Arrange - create two users
        from tests.factories import UserFactory
        from quota_management.models import UserQuota

        user1 = UserFactory()
        user2 = UserFactory()

        UserQuota.objects.update_or_create(
            user=user1, defaults=dict(quota_limit=2, period="day")
        )
        UserQuota.objects.update_or_create(
            user=user2, defaults=dict(quota_limit=2, period="day")
        )

        # Max out user1's quota
        for i in range(2):
            DiagramGenerationLogFactory(user=user1)

        # Act - user2 should still be able to make requests
        api_client.force_authenticate(user=user2)
        response = api_client.post(diagrams_url, {"text": "test"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
