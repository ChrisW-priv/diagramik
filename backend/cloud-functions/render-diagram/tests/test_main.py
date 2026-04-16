"""Tests for the render-diagram Cloud Function."""

import json
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-diagrams-bucket")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")

    import importlib
    import sys

    # Remove cached module so env vars are re-read
    sys.modules.pop("main", None)

    import main  # noqa: F401 — side effect: registers the function
    import functions_framework

    return functions_framework.create_app(target="main", source="main.py")


@pytest.fixture
def client(app):
    return app.test_client()


def _post(client, body):
    return client.post(
        "/",
        data=json.dumps(body),
        content_type="application/json",
    )


class TestMissingFields:
    def test_missing_type_returns_400(self, client):
        resp = _post(client, {"code": "flowchart TD\nA-->B"})
        assert resp.status_code == 400

    def test_missing_code_returns_400(self, client):
        resp = _post(client, {"type": "mermaid"})
        assert resp.status_code == 400

    def test_unknown_type_returns_400(self, client):
        resp = _post(client, {"type": "unknown", "code": "something"})
        assert resp.status_code == 400


class TestMermaidDiagram:
    def test_success_returns_uri(self, client):
        mock_blob = MagicMock()
        mock_blob.bucket.name = "test-diagrams-bucket"
        mock_blob.name = "output.svg"

        with (
            patch("renderer.mermaid.draw_mermaid_diagram", return_value={"path": "/tmp/out.svg", "format": "svg"}),
            patch("renderer.gcs.move_file_to_gcs", return_value=mock_blob),
        ):
            resp = _post(client, {"type": "mermaid", "code": "flowchart TD\nA-->B", "title": "Test"})

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["uri"].startswith("gs://")
        assert data["title"] == "Test"

    def test_mermaid_render_error_returns_422(self, client):
        with patch("renderer.mermaid.draw_mermaid_diagram", return_value={"error": "bad syntax", "format": "svg"}):
            resp = _post(client, {"type": "mermaid", "code": "invalid"})

        assert resp.status_code == 422
        data = json.loads(resp.data)
        assert "error" in data


class TestArchitectureDiagram:
    def test_success_returns_uri(self, client):
        mock_blob = MagicMock()
        mock_blob.bucket.name = "test-diagrams-bucket"
        mock_blob.name = "output.png"

        with (
            patch("renderer.architecture.draw_architecture_diagram"),
            patch("renderer.gcs.move_file_to_gcs", return_value=mock_blob),
        ):
            resp = _post(client, {"type": "architecture", "code": "pass", "title": "Arch"})

        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["uri"].startswith("gs://")
        assert data["title"] == "Arch"
