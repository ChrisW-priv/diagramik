"""Shared fixtures for render-diagram cloud function tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_gcs_blob():
    blob = MagicMock()
    blob.bucket.name = "test-diagrams-bucket"
    blob.name = "test-file.svg"
    return blob


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-diagrams-bucket")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")

    import importlib
    import main as m
    importlib.reload(m)

    import functions_framework
    return functions_framework.create_app(target="main", source="main.py").test_client()
