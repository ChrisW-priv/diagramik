import os
from django.conf import settings

BASE_DIR = settings.BASE_DIR

# FastAgent configuration paths
FAST_AGENT_CONFIG_FILEPATH = os.environ.get(
    "FAST_AGENT_CONFIG_FILEPATH",
    BASE_DIR.parent / "fast-agent-config" / "fastagent.config.yaml",
)

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "playground-449613")
DIAGRAMS_BUCKET_NAME = os.environ.get("DIAGRAMS_BUCKET_NAME", "diagramik-diagrams")

SIGNED_URL_SA_KEY_FILENAME = os.environ.get("SIGNED_URL_SA_KEY_FILENAME")
