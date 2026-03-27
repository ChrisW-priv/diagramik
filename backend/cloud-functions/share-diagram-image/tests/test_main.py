import os
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

import main as cf_main


def make_request(path="/share/some-token"):
    app = Flask(__name__)
    with app.test_request_context(path):
        from flask import request
        return request


class TestMain:
    def _call(self, path, monolith_response_status=200, monolith_response_json=None, image_uri=None):
        """Helper to call the Cloud Function with a mocked monolith response."""
        mock_resp = MagicMock()
        mock_resp.status_code = monolith_response_status
        mock_resp.ok = monolith_response_status < 400
        if monolith_response_json is not None:
            mock_resp.json.return_value = monolith_response_json
        elif image_uri is not None:
            mock_resp.json.return_value = {"image_uri": image_uri}

        app = Flask(__name__)
        with app.test_request_context(path):
            from flask import request
            with patch("requests.get", return_value=mock_resp):
                return cf_main.main(request)

    def test_redirect_plain_url(self):
        """Returns 302 redirect for a plain https:// image URI."""
        image_url = "https://example.com/image.png"
        response = self._call("/share/abc123", image_uri=image_url)
        assert response.status_code == 302
        assert response.headers["Location"] == image_url

    def test_redirect_gs_uri(self):
        """Generates a signed URL and redirects when image_uri is gs://."""
        signed_url = "https://storage.googleapis.com/signed"
        with patch.object(cf_main, "_get_signed_url", return_value=signed_url) as mock_sign:
            response = self._call("/share/abc123", image_uri="gs://bucket/image.png")
        assert response.status_code == 302
        assert response.headers["Location"] == signed_url
        mock_sign.assert_called_once_with("gs://bucket/image.png")

    def test_404_when_token_not_found(self):
        """Returns 404 when the monolith returns 404."""
        result = self._call("/share/missing-token", monolith_response_status=404)
        body, status_code = result
        assert status_code == 404

    def test_400_when_no_token(self):
        """Returns 400 when no token is present in the path."""
        app = Flask(__name__)
        with app.test_request_context("/"):
            from flask import request
            with patch("requests.get") as mock_get:
                result = cf_main.main(request)
        body, status_code = result
        assert status_code == 400

    def test_502_when_monolith_error(self):
        """Returns 502 when the monolith returns a server error."""
        result = self._call("/share/some-token", monolith_response_status=500)
        body, status_code = result
        assert status_code == 502
