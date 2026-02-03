"""End-to-end integration tests for complete user journeys."""

import pytest
from rest_framework import status
from django.contrib.auth import get_user_model
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
        mock_agent_call.assert_called_once()

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
        assert mock_agent_call.call_count == 2

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
        mock_gcs_signed_url.assert_called_once()

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
        """
        Test flow: User with OAuth account -> Create multiple diagrams.
        This test verifies that users with social accounts can create diagrams
        """

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

        # Verify agent was called twice
        assert mock_agent_call.call_count == 2
