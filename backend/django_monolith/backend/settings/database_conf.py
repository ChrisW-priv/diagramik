from django.conf import settings


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": settings.BASE_DIR / "db.sqlite3",
    }
}
