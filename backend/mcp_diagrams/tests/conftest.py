"""Shared pytest fixtures for MCP diagrams service tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
import os


@pytest.fixture
def mock_gcs_client(mocker):
    """Mock Google Cloud Storage client."""
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_blob.bucket.name = "test-bucket"
    mock_blob.name = "test-file.png"
    # Mock the upload_from_filename method to not actually open files
    mock_blob.upload_from_filename = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_client.bucket.return_value = mock_bucket

    mocker.patch("move_file_to_gcs.Client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_file_system(mocker, tmp_path):
    """Mock file system operations for testing diagram generation."""
    # Create a temporary directory for test files
    test_file = tmp_path / "test_diagram.png"
    test_file.write_text("fake image data")

    # Mock os.remove to prevent actual file deletion
    mock_remove = mocker.patch("os.remove")

    return {
        "tmp_path": tmp_path,
        "test_file": test_file,
        "mock_remove": mock_remove,
    }


@pytest.fixture
def mock_diagram_library(mocker):
    """Mock the diagrams library to avoid actual diagram generation."""
    mock_diagram = MagicMock()
    mocker.patch("draw_diagram.Diagram", return_value=mock_diagram)

    # Mock the context manager
    mock_diagram.__enter__ = MagicMock(return_value=mock_diagram)
    mock_diagram.__exit__ = MagicMock(return_value=None)

    return mock_diagram


@pytest.fixture
def sample_mermaid_code():
    """Provide sample Mermaid diagram code for testing."""
    return """flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E"""


@pytest.fixture
def sample_diagram_code():
    """Provide sample Python diagrams code for testing."""
    return """
user = User("User")
browser = Client("Browser")
with Cluster("Our VPC"):
    lb = LoadBalancing("Load Balancer")
    lb >> [Run("CloudRun Service"), Storage("GCS Bucket")]
user >> browser >> lb
"""


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")


@pytest.fixture
def mcp_server():
    """Provide access to the MCP server instance."""
    # Import here to avoid issues with environment variables
    os.environ["BUCKET_NAME"] = "test-bucket"
    os.environ["GCP_PROJECT_ID"] = "test-project"

    from server import mcp

    return mcp


@pytest.fixture
async def mock_mcp_context():
    """Mock MCP context for tool execution."""
    context = AsyncMock()
    context.request_context = {}
    return context
