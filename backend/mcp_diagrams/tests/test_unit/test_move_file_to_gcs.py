"""Unit tests for GCS file upload - simplified version."""

import pytest
from unittest.mock import MagicMock, patch
from move_file_to_gcs import move_file_to_gcs


pytestmark = pytest.mark.unit


class TestMoveFileToGCS:
    """Tests for the move_file_to_gcs function."""

    def test_move_file_to_gcs_basic_flow(self, tmp_path):
        """Test basic upload flow with temp file."""
        # Arrange - create actual temp file
        test_file = tmp_path / "test.png"
        test_file.write_text("fake image data")
        filename = str(test_file)

        with patch("move_file_to_gcs.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()

            mock_blob.bucket.name = "my-bucket"
            mock_blob.name = "test.png"
            mock_blob.upload_from_filename = MagicMock()  # Don't actually upload

            mock_bucket.blob.return_value = mock_blob
            mock_client.bucket.return_value = mock_bucket
            mock_client_class.return_value = mock_client

            # Act
            result = move_file_to_gcs(filename, "my-bucket", "my-project")

            # Assert
            assert result == mock_blob
            mock_client_class.assert_called_once_with(project="my-project")
            mock_client.bucket.assert_called_once_with("my-bucket")
            mock_blob.upload_from_filename.assert_called_once_with(filename)

    def test_move_file_to_gcs_uses_env_var_project_id(self, tmp_path):
        """Test that it uses environment variable when project_id is None."""
        # Arrange
        test_file = tmp_path / "test.png"
        test_file.write_text("data")
        filename = str(test_file)

        with (
            patch("move_file_to_gcs.Client") as mock_client_class,
            patch("move_file_to_gcs.GCP_PROJECT_ID", "env-project"),
        ):
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_blob.upload_from_filename = MagicMock()

            mock_bucket.blob.return_value = mock_blob
            mock_client.bucket.return_value = mock_bucket
            mock_client_class.return_value = mock_client

            # Act
            move_file_to_gcs(filename, "bucket", project_id=None)

            # Assert
            mock_client_class.assert_called_once_with(project="env-project")

    def test_move_file_to_gcs_removes_file_after_upload(self, tmp_path):
        """Test that local file is removed after successful upload."""
        # Arrange
        test_file = tmp_path / "to_remove.png"
        test_file.write_text("data")
        filename = str(test_file)

        with patch("move_file_to_gcs.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_blob.upload_from_filename = MagicMock()

            mock_bucket.blob.return_value = mock_blob
            mock_client.bucket.return_value = mock_bucket
            mock_client_class.return_value = mock_client

            # Verify file exists
            assert test_file.exists()

            # Act
            move_file_to_gcs(filename, "bucket", "project")

            # Assert - file should be removed
            assert not test_file.exists()


class TestMoveFileToGCSMocked:
    """Tests using the mock_gcs_client fixture."""

    def test_with_fixture(self, mock_gcs_client, tmp_path):
        """Test using the shared GCS fixture."""
        # Arrange
        test_file = tmp_path / "fixture_test.png"
        test_file.write_text("data")

        with patch("os.remove"):
            # Act
            result = move_file_to_gcs(str(test_file), "test-bucket", "test-project")

            # Assert
            assert result is not None
            assert result.bucket.name == "test-bucket"
