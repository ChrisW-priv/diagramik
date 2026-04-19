"""Tests for user account deletion endpoint."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.factories import DiagramFactory, DiagramVersionFactory

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestUserDelete:
    """Tests for DELETE /api/v1/auth/user/ endpoint."""

    @pytest.fixture
    def user_url(self):
        return "/api/v1/auth/user/"

    def test_delete_requires_authentication(self, api_client, user_url):
        response = api_client.delete(user_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_backs_up_and_deletes_user(
        self, authenticated_client, user, mocker, user_url
    ):
        diagram = DiagramFactory(owner=user)
        DiagramVersionFactory(diagram=diagram)

        mock_backup = mocker.patch(
            "user_auth.views.email_password_auth.user._backup_user_diagrams_to_gcs"
        )

        response = authenticated_client.delete(user_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_backup.assert_called_once_with(user)
        assert not User.objects.filter(pk=user.pk).exists()

    def test_delete_with_no_diagrams_backs_up_and_deletes(
        self, authenticated_client, user, mocker, user_url
    ):
        mock_backup = mocker.patch(
            "user_auth.views.email_password_auth.user._backup_user_diagrams_to_gcs"
        )

        response = authenticated_client.delete(user_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_backup.assert_called_once_with(user)
        assert not User.objects.filter(pk=user.pk).exists()

    def test_delete_returns_503_when_gcs_fails(
        self, authenticated_client, user, mocker, user_url
    ):
        mocker.patch(
            "user_auth.views.email_password_auth.user._backup_user_diagrams_to_gcs",
            side_effect=Exception("GCS unavailable"),
        )

        response = authenticated_client.delete(user_url)

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "detail" in response.data

    def test_delete_does_not_delete_user_when_gcs_fails(
        self, authenticated_client, user, mocker, user_url
    ):
        mocker.patch(
            "user_auth.views.email_password_auth.user._backup_user_diagrams_to_gcs",
            side_effect=Exception("GCS unavailable"),
        )

        authenticated_client.delete(user_url)

        assert User.objects.filter(pk=user.pk).exists()
