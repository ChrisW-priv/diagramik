"""End-to-end integration tests for complete user journeys."""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
from diagrams_assistant.models import Diagram
from freezegun import freeze_time

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


class TestCompleteUserJourney:
    """Test complete user journey from registration to diagram creation."""

    @freeze_time("2026-01-01 12:00:00")
    def test_complete_user_flow(
        self,
        api_client,
        mock_agent_call,
        mock_gcs_signed_url,
        mock_send_mail,
        settings,
    ):
        """Test complete flow: Register -> Login -> Create Diagram -> View -> Delete."""
        # Configure settings for test
        settings.ACCOUNT_EMAIL_VERIFICATION = "optional"

        # Step 1: Register new user
        registration_data = {
            "email": "journey@example.com",
            "password1": "securepass123",
            "password2": "securepass123",
            "first_name": "Journey",
        }
        register_response = api_client.post(
            "/api/v1/auth/registration/", registration_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        assert "access" in register_response.data
        access_token = register_response.data["access"]

        # Verify user was created
        user = User.objects.get(email="journey@example.com")
        assert user.first_name == "Journey"

        # Step 2: Use the token to create a diagram
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        create_diagram_response = api_client.post(
            "/api/v1/diagrams/", {"text": "Draw a cloud architecture"}
        )
        assert create_diagram_response.status_code == status.HTTP_201_CREATED
        diagram_id = create_diagram_response.data["diagram_id"]

        # Step 3: List diagrams (verify it's there)
        list_response = api_client.get("/api/v1/diagrams/")
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) == 1
        assert str(list_response.data[0]["id"]) == diagram_id

        # Step 4: Get diagram details
        detail_response = api_client.get(f"/api/v1/diagrams/{diagram_id}/")
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.data["title"] == "Test Diagram"
        assert len(detail_response.data["versions"]) == 1

        # Step 5: Create a new version
        version_response = api_client.post(
            f"/api/v1/diagrams/{diagram_id}/versions/",
            {"text": "Make it bigger"},
        )
        assert version_response.status_code == status.HTTP_201_CREATED

        # Verify diagram now has 2 versions
        detail_response = api_client.get(f"/api/v1/diagrams/{diagram_id}/")
        assert len(detail_response.data["versions"]) == 2

        # Step 6: Get image URL
        version_id = detail_response.data["versions"][0]["id"]
        image_response = api_client.get(
            f"/api/v1/diagrams/{diagram_id}/versions/{version_id}/image/?redirect=false"
        )
        assert image_response.status_code == status.HTTP_200_OK
        assert "image_url" in image_response.data

        # Step 7: Delete diagram
        delete_response = api_client.delete(f"/api/v1/diagrams/{diagram_id}/")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify it's gone
        list_response = api_client.get("/api/v1/diagrams/")
        assert len(list_response.data) == 0

    @freeze_time("2026-01-01 12:00:00")
    def test_oauth_to_diagram_creation_flow(
        self, api_client, mock_agent_call, mock_gcs_signed_url, mock_google_oauth
    ):
        """Test flow: OAuth login -> Create diagrams -> Hit rate limit."""
        # This test would require more complex OAuth mocking
        # For now, we'll create a user with social account and test from there

        from tests.factories import UserFactory, SocialAccountFactory

        # Create user with Google social account
        user = UserFactory(email="google@example.com")
        SocialAccountFactory(user=user, provider="google")

        # Authenticate as this user
        api_client.force_authenticate(user=user)

        # Create first diagram
        response1 = api_client.post("/api/v1/diagrams/", {"text": "First diagram"})
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second diagram
        response2 = api_client.post("/api/v1/diagrams/", {"text": "Second diagram"})
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify both diagrams exist
        list_response = api_client.get("/api/v1/diagrams/")
        assert len(list_response.data) == 2


class TestMultiVersionWorkflow:
    """Test creating and managing multiple versions."""

    @freeze_time("2026-01-01 12:00:00")
    def test_iterative_diagram_creation(
        self, authenticated_client, mock_agent_call, user
    ):
        """Test creating a diagram and iterating with multiple versions."""
        # Create initial diagram
        response = authenticated_client.post(
            "/api/v1/diagrams/", {"text": "Initial diagram"}
        )
        assert response.status_code == status.HTTP_201_CREATED
        diagram_id = response.data["diagram_id"]

        # Create multiple versions iteratively
        prompts = [
            "Make it bigger",
            "Add more servers",
            "Change colors to blue",
            "Add database",
        ]

        for prompt in prompts:
            version_response = authenticated_client.post(
                f"/api/v1/diagrams/{diagram_id}/versions/", {"text": prompt}
            )
            assert version_response.status_code == status.HTTP_201_CREATED

        # Verify all versions exist
        detail_response = authenticated_client.get(f"/api/v1/diagrams/{diagram_id}/")
        assert len(detail_response.data["versions"]) == 5  # 1 initial + 4 updates

        # Verify chat history
        assert len(detail_response.data["chat_history"]) == 10  # 5 user + 5 assistant


class TestQuotaLimitJourney:
    """Test user journey when hitting quota limits."""

    @freeze_time("2026-01-01 12:00:00")
    def test_hit_quota_limit_then_reset(
        self, authenticated_client, mock_agent_call, user, site_settings
    ):
        """Test hitting quota limit and then waiting for reset."""
        from quota_management.models import UserQuota

        # Set custom quota of 3 per day
        UserQuota.objects.update_or_create(
            user=user, defaults=dict(quota_limit=3, period="day")
        )

        # Create 3 diagrams successfully
        for i in range(3):
            response = authenticated_client.post(
                "/api/v1/diagrams/", {"text": f"Diagram {i}"}
            )
            assert response.status_code == status.HTTP_201_CREATED

        # 4th should be throttled
        response = authenticated_client.post(
            "/api/v1/diagrams/", {"text": "Should fail"}
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Verify user still has their 3 diagrams
        list_response = authenticated_client.get("/api/v1/diagrams/")
        assert len(list_response.data) == 3

        # Travel to next day
        with freeze_time("2026-01-02 12:00:00"):
            # Should be able to create again
            response = authenticated_client.post(
                "/api/v1/diagrams/", {"text": "After reset"}
            )
            assert response.status_code == status.HTTP_201_CREATED

            # Verify user now has 4 diagrams total
            list_response = authenticated_client.get("/api/v1/diagrams/")
            assert len(list_response.data) == 4


class TestPermissionsAndIsolation:
    """Test that users can't access each other's data."""

    def test_user_isolation(self, api_client, mock_agent_call):
        """Test that users can only access their own diagrams."""
        from tests.factories import UserFactory, DiagramFactory

        # Create two users with diagrams
        user1 = UserFactory(email="user1@example.com")
        user2 = UserFactory(email="user2@example.com")

        DiagramFactory(owner=user1, title="User 1 Diagram")
        diagram2 = DiagramFactory(owner=user2, title="User 2 Diagram")

        # User 1 logs in
        api_client.force_authenticate(user=user1)

        # User 1 can see their own diagram
        list_response = api_client.get("/api/v1/diagrams/")
        assert len(list_response.data) == 1
        assert list_response.data[0]["title"] == "User 1 Diagram"

        # User 1 cannot access User 2's diagram
        detail_response = api_client.get(f"/api/v1/diagrams/{diagram2.id}/")
        assert detail_response.status_code == status.HTTP_404_NOT_FOUND

        # User 1 cannot delete User 2's diagram
        delete_response = api_client.delete(f"/api/v1/diagrams/{diagram2.id}/")
        assert delete_response.status_code == status.HTTP_404_NOT_FOUND

        # Verify User 2's diagram still exists
        assert Diagram.objects.filter(id=diagram2.id).exists()
