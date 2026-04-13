import os
from datetime import timedelta

import functions_framework
import psycopg
from flask import Request, redirect

from google.cloud.storage import Client, Blob
from google.oauth2 import service_account


def _get_signed_url(image_uri: str) -> str:
    cred = service_account.Credentials.from_service_account_file(
        os.environ["SIGNED_URL_SA_KEY_FILENAME"]
    )
    storage_client = Client(credentials=cred)
    blob = Blob.from_uri(image_uri, storage_client)
    return blob.generate_signed_url(expiration=timedelta(hours=1))


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
