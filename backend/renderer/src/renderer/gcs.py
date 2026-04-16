import os

from google.cloud.storage import Client, Blob


# Environment configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "playground-449613")


def move_file_to_gcs(
    filename: str, bucket_name: str, project_id: str | None = None
) -> Blob:
    """Move a local file to Google Cloud Storage and remove the local copy.

    Args:
        filename: Local file path to upload
        bucket_name: Target GCS bucket name
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)

    Returns:
        The uploaded Blob object
    """
    project = project_id or GCP_PROJECT_ID
    client = Client(project=project)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename)
    os.remove(filename)
    return blob
