"""Tests for diagram version operations."""

import pytest
from rest_framework import status
from diagrams_assistant.models import DiagramVersion, ChatMessage
from tests.factories import DiagramFactory, DiagramVersionFactory

pytestmark = pytest.mark.django_db


class TestDiagramVersionCreate:
    """Tests for creating diagram versions."""

    @pytest.fixture
    def user_diagram(self, user):
        """Create a diagram with existing history."""
        diagram = DiagramFactory(owner=user, agent_history='{"history": ["previous"]}')
        DiagramVersionFactory(diagram=diagram, prompt_text="Initial version")
        return diagram

    @pytest.fixture
    def version_url(self, user_diagram):
        return f"/api/v1/diagrams/{user_diagram.id}/versions/"

    def test_create_version_adds_to_existing_diagram(
        self, authenticated_client, version_url, user_diagram, mock_agent_call
    ):
        """Test that creating a version adds to existing diagram."""
        # Arrange
        version_data = {"text": "Make it bigger"}

        # Act
        response = authenticated_client.post(version_url, version_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        mock_agent_call.assert_called_once()
        assert DiagramVersion.objects.filter(diagram=user_diagram).count() == 2

    def test_create_version_preserves_agent_history(
        self, authenticated_client, version_url, user_diagram, mock_agent_call
    ):
        """Test that creating a version preserves and updates agent history."""
        # Arrange
        original_history = user_diagram.agent_history
        version_data = {"text": "Make it bigger"}

        # Act
        response = authenticated_client.post(version_url, version_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        user_diagram.refresh_from_db()
        # History should be updated (mocked to return new history)
        assert user_diagram.agent_history == '{"history": []}'
        # Agent was called with previous history
        mock_agent_call.assert_called_once()
        call_args = mock_agent_call.call_args
        assert call_args[1]["previous_history_json"] == original_history

    def test_create_version_increments_chat_messages(
        self, authenticated_client, version_url, user_diagram, mock_agent_call
    ):
        """Test that creating a version adds chat messages."""
        # Arrange
        initial_message_count = ChatMessage.objects.filter(diagram=user_diagram).count()
        version_data = {"text": "Make it bigger"}

        # Act
        response = authenticated_client.post(version_url, version_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        mock_agent_call.assert_called_once()
        messages = ChatMessage.objects.filter(diagram=user_diagram).order_by(
            "created_at"
        )
        # Should add 2 messages (user + assistant)
        assert messages.count() == initial_message_count + 2
        assert messages.last().role == "assistant"
        assert messages.last().content == "Image Ready!"

    def test_create_version_without_text_returns_400(
        self, authenticated_client, version_url
    ):
        """Test that creating a version without text returns 400."""
        # Arrange
        version_data = {}

        # Act
        response = authenticated_client.post(version_url, version_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    def test_create_version_for_other_user_diagram_returns_404(
        self, authenticated_client, mock_agent_call
    ):
        """Test that creating a version for another user's diagram returns 404."""
        # Arrange
        other_user_diagram = DiagramFactory()  # Different user
        url = f"/api/v1/diagrams/{other_user_diagram.id}/versions/"
        version_data = {"text": "Make it bigger"}

        # Act
        response = authenticated_client.post(url, version_data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_version_requires_authentication(self, api_client, version_url):
        """Test that creating a version requires authentication."""
        # Arrange
        version_data = {"text": "Make it bigger"}

        # Act
        response = api_client.post(version_url, version_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDiagramVersionDelete:
    """Tests for deleting diagram versions."""

    @pytest.fixture
    def user_diagram_with_versions(self, user):
        """Create a diagram with multiple versions."""
        diagram = DiagramFactory(owner=user)
        version1 = DiagramVersionFactory(diagram=diagram, prompt_text="Version 1")
        version2 = DiagramVersionFactory(diagram=diagram, prompt_text="Version 2")
        return diagram, version1, version2

    def test_delete_version_removes_from_database(
        self, authenticated_client, user_diagram_with_versions
    ):
        """Test that deleting a version removes it from database."""
        # Arrange
        diagram, version1, version2 = user_diagram_with_versions
        url = f"/api/v1/diagrams/{diagram.id}/versions/{version1.id}/"
        version1_id = version1.id

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not DiagramVersion.objects.filter(id=version1_id).exists()
        # Other version should still exist
        assert DiagramVersion.objects.filter(id=version2.id).exists()

    def test_delete_version_from_other_user_diagram_returns_404(
        self, authenticated_client
    ):
        """Test that deleting a version from another user's diagram returns 404."""
        # Arrange
        other_user_diagram = DiagramFactory()
        other_user_version = DiagramVersionFactory(diagram=other_user_diagram)
        url = f"/api/v1/diagrams/{other_user_diagram.id}/versions/{other_user_version.id}/"

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert DiagramVersion.objects.filter(id=other_user_version.id).exists()

    def test_delete_version_requires_authentication(
        self, api_client, user_diagram_with_versions
    ):
        """Test that deleting a version requires authentication."""
        # Arrange
        diagram, version1, version2 = user_diagram_with_versions
        url = f"/api/v1/diagrams/{diagram.id}/versions/{version1.id}/"

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert DiagramVersion.objects.filter(id=version1.id).exists()


class TestDiagramVersionImage:
    """Tests for getting diagram version images."""

    @pytest.fixture
    def user_diagram_with_version(self, user):
        """Create a diagram with a version."""
        diagram = DiagramFactory(owner=user)
        version = DiagramVersionFactory(
            diagram=diagram, image_uri="gs://test-bucket/test-image.png"
        )
        return diagram, version

    def test_get_image_url_returns_signed_url(
        self, authenticated_client, user_diagram_with_version, mock_gcs_signed_url
    ):
        """Test that getting image URL returns signed URL."""
        # Arrange
        diagram, version = user_diagram_with_version
        url = f"/api/v1/diagrams/{diagram.id}/versions/{version.id}/image/"

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_302_FOUND
        mock_gcs_signed_url.assert_called_once()

    def test_get_image_url_with_redirect_false_returns_json(
        self, authenticated_client, user_diagram_with_version, mock_gcs_signed_url
    ):
        """Test that getting image URL with redirect=false returns JSON."""
        # Arrange
        diagram, version = user_diagram_with_version
        url = (
            f"/api/v1/diagrams/{diagram.id}/versions/{version.id}/image/?redirect=false"
        )

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "image_url" in response.data
        mock_gcs_signed_url.assert_called_once()

    def test_get_image_url_from_other_user_version_returns_404(
        self, authenticated_client
    ):
        """Test that getting image URL from another user's version returns 404."""
        # Arrange
        other_user_diagram = DiagramFactory()
        other_user_version = DiagramVersionFactory(diagram=other_user_diagram)
        url = f"/api/v1/diagrams/{other_user_diagram.id}/versions/{other_user_version.id}/image/"

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_image_url_requires_authentication(
        self, api_client, user_diagram_with_version
    ):
        """Test that getting image URL requires authentication."""
        # Arrange
        diagram, version = user_diagram_with_version
        url = f"/api/v1/diagrams/{diagram.id}/versions/{version.id}/image/"

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
