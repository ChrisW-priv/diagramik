import os
from datetime import timedelta

import functions_framework
import requests
from flask import Request, redirect

import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud.storage import Client, Blob


def _get_signed_url(image_uri: str) -> str:
    credentials, _ = google.auth.default()
    credentials.refresh(GoogleAuthRequest())
    storage_client = Client(credentials=credentials)
    blob = Blob.from_uri(image_uri, storage_client)
    return blob.generate_signed_url(expiration=timedelta(hours=1), credentials=credentials)


@functions_framework.http
def main(request: Request):
    # Extract token from path: /share/{token}
    token = request.path.strip("/").split("/")[-1]
    if not token:
        return "Token required", 400

    monolith_url = os.environ["MONOLITH_URL"]
    resp = requests.get(f"{monolith_url}/api/v1/share/{token}/", timeout=10)
    if resp.status_code == 404:
        return "Share link not found", 404
    if not resp.ok:
        return "Error resolving share link", 502

    image_uri = resp.json()["image_uri"]
    if image_uri.startswith("gs://"):
        image_uri = _get_signed_url(image_uri)

    return redirect(image_uri, code=302)
