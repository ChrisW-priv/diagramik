import os
from datetime import timedelta

import functions_framework
import psycopg
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


def _get_image_uri(token: str) -> str | None:
    with psycopg.connect(
        host=os.environ["DB_PRIVATE_IP"],
        dbname=os.environ["POSTGRES_DATABASE_NAME"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    ) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT dv.image_uri"
            " FROM diagrams_assistant_diagramsharelink dsl"
            " JOIN diagrams_assistant_diagramversion dv ON dsl.diagram_version_id = dv.id"
            " WHERE dsl.token = %s",
            (str(token),),
        )
        row = cur.fetchone()
    return row[0] if row else None


@functions_framework.http
def main(request: Request):
    # Extract token from path: /share/{token}
    token = request.path.strip("/").split("/")[-1]
    if not token:
        return "Token required", 400

    image_uri = _get_image_uri(token)
    if image_uri is None:
        return "Share link not found", 404

    if image_uri.startswith("gs://"):
        image_uri = _get_signed_url(image_uri)

    return redirect(image_uri, code=302)
