"""Tests for quota period calculations and resets."""

import pytest
from rest_framework import status
from freezegun import freeze_time
from tests.factories import DiagramGenerationLogFactory
from site_settings.models import SiteSettings

pytestmark = pytest.mark.django_db


class TestDailyQuotaReset:
    """Tests for daily quota reset."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def site_settings(self):
        """Create site settings."""
        settings, _ = SiteSettings.objects.get_or_create(id=1)
        return settings

    @freeze_time("2026-01-01 12:00:00")
    def test_daily_quota_resets_after_24_hours(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that daily quota resets after 24 hours."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="day")
        )

        # Make 3 requests (hit limit)
        for i in range(3):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel forward 24 hours + 1 second
        with freeze_time("2026-01-02 12:00:01"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

    @freeze_time("2026-01-01 23:59:59")
    def test_daily_quota_resets_at_midnight(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that daily quota resets at midnight."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="day")
        )

        # Make 2 requests just before midnight
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel to midnight (new day)
        with freeze_time("2026-01-02 00:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED


class TestWeeklyQuotaReset:
    """Tests for weekly quota reset."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def site_settings(self):
        settings, _ = SiteSettings.objects.get_or_create(id=1)
        return settings

    @freeze_time("2026-01-05 12:00:00")  # Monday
    def test_weekly_quota_resets_after_7_days(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that weekly quota resets after 7 days."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="week")
        )

        # Make 3 requests (hit limit)
        for i in range(3):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel forward 7 days to next Monday
        with freeze_time("2026-01-12 12:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

    @freeze_time("2026-01-08 23:59:59")  # Thursday night
    def test_weekly_quota_resets_on_monday(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that weekly quota resets on Monday at 00:00."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="week")
        )

        # Make 2 requests (hit limit)
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel to next Monday at 00:00
        with freeze_time("2026-01-12 00:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED


class TestMonthlyQuotaReset:
    """Tests for monthly quota reset."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def site_settings(self):
        settings, _ = SiteSettings.objects.get_or_create(id=1)
        return settings

    @freeze_time("2026-01-15 12:00:00")
    def test_monthly_quota_resets_on_first_of_month(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that monthly quota resets on the first of the month."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="month")
        )

        # Make 3 requests (hit limit)
        for i in range(3):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel to first of next month
        with freeze_time("2026-02-01 00:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

    @freeze_time("2026-01-31 23:59:59")
    def test_monthly_quota_resets_across_month_boundary(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that monthly quota resets when month changes."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="month")
        )

        # Make 2 requests (hit limit)
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel to next month (February)
        with freeze_time("2026-02-01 00:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED

    @freeze_time("2026-02-28 12:00:00")
    def test_monthly_quota_handles_february(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that monthly quota properly handles February."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=2, period="month")
        )

        # Make 2 requests (hit limit)
        for i in range(2):
            DiagramGenerationLogFactory(user=user)

        # Verify we're throttled
        response = authenticated_client.post(diagrams_url, {"text": "test 1"})
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Act - travel to March
        with freeze_time("2026-03-01 00:00:00"):
            response = authenticated_client.post(diagrams_url, {"text": "test 2"})

            # Assert
            assert response.status_code == status.HTTP_201_CREATED


class TestQuotaPeriodCounting:
    """Tests for accurate quota counting within periods."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    @pytest.fixture
    def site_settings(self):
        settings, _ = SiteSettings.objects.get_or_create(id=1)
        return settings

    @freeze_time("2026-01-01 12:00:00")
    def test_quota_counts_only_current_period(
        self, authenticated_client, diagrams_url, mock_agent_call, user, site_settings
    ):
        """Test that quota only counts generations from current period."""
        # Arrange
        from quota_management.models import UserQuota

        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="day")
        )

        # Make 2 requests on day 1
        with freeze_time("2026-01-01 12:00:00"):
            for i in range(2):
                DiagramGenerationLogFactory(user=user)

        # Make 2 requests on day 2 (should not count day 1)
        with freeze_time("2026-01-02 12:00:00"):
            response1 = authenticated_client.post(diagrams_url, {"text": "test 1"})
            response2 = authenticated_client.post(diagrams_url, {"text": "test 2"})
            response3 = authenticated_client.post(diagrams_url, {"text": "test 3"})

            # Assert - first 3 should succeed (day 1 doesn't count)
            assert response1.status_code == status.HTTP_201_CREATED
            assert response2.status_code == status.HTTP_201_CREATED
            assert response3.status_code == status.HTTP_201_CREATED

            # 4th request should be throttled
            response4 = authenticated_client.post(diagrams_url, {"text": "test 4"})
            assert response4.status_code == status.HTTP_429_TOO_MANY_REQUESTS
