import os
from pathlib import Path
from django.conf import settings

BASE_DIR: Path = settings.BASE_DIR

MEDIA_BUCKET_NAME = os.environ.get("DIAGRAMS_BUCKET_NAME", None)
PRIVATE_MOUNT = BASE_DIR.parent / "data" / "private"
MEDIA_FOLDER_NAME = "uploads"
MEDIA_ROOT = PRIVATE_MOUNT / MEDIA_FOLDER_NAME

if settings.DEBUG:
    MEDIA_URL = "/media/"
else:
    MEDIA_URL = (
        f"https://storage.googleapis.com/{MEDIA_BUCKET_NAME}/{MEDIA_FOLDER_NAME}/"
    )
