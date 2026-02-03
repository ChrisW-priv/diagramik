"""Tests for diagram CRUD operations."""

import pytest
from rest_framework import status
from diagrams_assistant.models import Diagram, DiagramVersion, ChatMessage
from tests.factories import DiagramFactory, DiagramVersionFactory

pytestmark = pytest.mark.django_db


class TestDiagramList:
    """Tests for listing diagrams."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    def test_list_diagrams_returns_only_user_diagrams(
        self, authenticated_client, diagrams_url, user
    ):
        """Test that list returns only diagrams owned by the authenticated user."""
        # Arrange
        DiagramFactory(owner=user, title="User Diagram 1")
        DiagramFactory(owner=user, title="User Diagram 2")
        DiagramFactory(title="Other User Diagram")

        # Act
        response = authenticated_client.get(diagrams_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        diagram_titles = [d["title"] for d in response.data]
        assert "User Diagram 1" in diagram_titles
        assert "User Diagram 2" in diagram_titles
        assert "Other User Diagram" not in diagram_titles

    def test_list_diagrams_empty_for_new_user(self, authenticated_client, diagrams_url):
        """Test that list returns empty array for user with no diagrams."""
        # Act
        response = authenticated_client.get(diagrams_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_diagrams_requires_authentication(self, api_client, diagrams_url):
        """Test that listing diagrams requires authentication."""
        # Act
        response = api_client.get(diagrams_url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDiagramCreate:
    """Tests for creating diagrams."""

    @pytest.fixture
    def diagrams_url(self):
        return "/api/v1/diagrams/"

    def test_create_diagram_with_valid_text_returns_201(
        self, authenticated_client, diagrams_url, mock_agent_call, user
    ):
        """Test that creating a diagram with valid text returns 201."""
        # Arrange
        diagram_data = {"text": "Draw a cloud architecture diagram"}

        # Act
        response = authenticated_client.post(diagrams_url, diagram_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert "diagram_id" in response.data
        mock_agent_call.assert_called_once()

    def test_create_diagram_creates_version_and_messages(
        self, authenticated_client, diagrams_url, mock_agent_call, user
    ):
        """Test that creating a diagram also creates version and chat messages."""
        # Arrange
        diagram_data = {"text": "Draw a cloud architecture diagram"}

        # Act
        response = authenticated_client.post(diagrams_url, diagram_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

        # Check diagram was created
        diagram = Diagram.objects.get(owner=user)
        assert diagram.title == "Test Diagram"  # From mock

        # Check version was created
        assert DiagramVersion.objects.filter(diagram=diagram).count() == 1
        version = DiagramVersion.objects.get(diagram=diagram)
        assert version.prompt_text == "Draw a cloud architecture diagram"

        # Check chat messages were created
        messages = ChatMessage.objects.filter(diagram=diagram).order_by("created_at")
        assert messages.count() == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Draw a cloud architecture diagram"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Image Ready!"

    def test_create_diagram_without_text_returns_400(
        self, authenticated_client, diagrams_url
    ):
        """Test that creating a diagram without text returns 400."""
        # Arrange
        diagram_data = {}

        # Act
        response = authenticated_client.post(diagrams_url, diagram_data)

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert "required" in response.data["error"].lower()

    def test_create_diagram_requires_authentication(self, api_client, diagrams_url):
        """Test that creating a diagram requires authentication."""
        # Arrange
        diagram_data = {"text": "Draw a cloud architecture diagram"}

        # Act
        response = api_client.post(diagrams_url, diagram_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDiagramDetail:
    """Tests for retrieving diagram details."""

    @pytest.fixture
    def diagram_url(self, user_diagram):
        return f"/api/v1/diagrams/{user_diagram.id}/"

    @pytest.fixture
    def user_diagram(self, user):
        return DiagramFactory(owner=user)

    def test_get_diagram_by_id_returns_full_details(
        self, authenticated_client, diagram_url, user_diagram
    ):
        """Test that getting a diagram returns full details."""
        # Arrange
        DiagramVersionFactory(diagram=user_diagram, prompt_text="Version 1")
        DiagramVersionFactory(diagram=user_diagram, prompt_text="Version 2")

        # Act
        response = authenticated_client.get(diagram_url)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(user_diagram.id)
        assert response.data["title"] == user_diagram.title
        assert len(response.data["versions"]) == 2

    def test_get_diagram_from_other_user_returns_404(self, authenticated_client, user):
        """Test that getting another user's diagram returns 404."""
        # Arrange
        other_user_diagram = DiagramFactory()  # Different user
        url = f"/api/v1/diagrams/{other_user_diagram.id}/"

        # Act
        response = authenticated_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_diagram_requires_authentication(self, api_client, user_diagram):
        """Test that getting a diagram requires authentication."""
        # Arrange
        url = f"/api/v1/diagrams/{user_diagram.id}/"

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDiagramDelete:
    """Tests for deleting diagrams."""

    @pytest.fixture
    def user_diagram(self, user):
        return DiagramFactory(owner=user)

    def test_delete_diagram_removes_from_database(
        self, authenticated_client, user_diagram
    ):
        """Test that deleting a diagram removes it from database."""
        # Arrange
        url = f"/api/v1/diagrams/{user_diagram.id}/"
        diagram_id = user_diagram.id

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Diagram.objects.filter(id=diagram_id).exists()

    def test_delete_diagram_from_other_user_returns_404(self, authenticated_client):
        """Test that deleting another user's diagram returns 404."""
        # Arrange
        other_user_diagram = DiagramFactory()  # Different user
        url = f"/api/v1/diagrams/{other_user_diagram.id}/"

        # Act
        response = authenticated_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Diagram.objects.filter(id=other_user_diagram.id).exists()

    def test_delete_diagram_requires_authentication(self, api_client, user_diagram):
        """Test that deleting a diagram requires authentication."""
        # Arrange
        url = f"/api/v1/diagrams/{user_diagram.id}/"

        # Act
        response = api_client.delete(url)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Diagram.objects.filter(id=user_diagram.id).exists()
