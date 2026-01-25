import os
from django.conf import settings


CORS_ALLOWED_ORIGINS = [
    "http://localhost:4321",
    "http://127.0.0.1:4321",
]

DEFUALT_FRONTEND_URL = (
    "http://localhost:4321" if settings.DEBUG else "https://diagramik.com"
)
FRONTEND_URL = os.environ.get("FRONTEND_URL", DEFUALT_FRONTEND_URL)

if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

# In debug mode, allow all origins for easier development
if settings.DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
