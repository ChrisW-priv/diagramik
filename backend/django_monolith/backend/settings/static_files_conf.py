import os
from pathlib import Path
from django.conf import settings

BASE_DIR: Path = settings.BASE_DIR

STATIC_BUCKET_NAME = os.environ.get("STATIC_BUCKET_NAME", None)
PUBLIC_MOUNT = BASE_DIR.parent / "data" / "public"
STATIC_FOLDER_NAME = "django-static"
STATIC_ROOT = PUBLIC_MOUNT / STATIC_FOLDER_NAME

if settings.DEBUG:
    STATIC_URL = "/static/"
else:
    STATIC_URL = (
        f"https://storage.googleapis.com/{STATIC_BUCKET_NAME}/{STATIC_FOLDER_NAME}/"
    )
