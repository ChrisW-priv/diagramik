import os
import warnings


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_DATABASE_NAME = os.getenv("POSTGRES_DATABASE_NAME", "postgres")


if db_ip := os.getenv("DB_PRIVATE_IP"):
    _DB_HOST = db_ip
else:
    warnings.warn(
        "You are connecting to a database via PUBLIC IP! (Are you sure this is safe?)"
    )
    db_conn_name = os.getenv("DB_CONN_NAME")
    pre_db_conn_name = os.getenv("PRE_DB_CONN_NAME", "/cloudsql/")
    _DB_HOST = f"{pre_db_conn_name}{db_conn_name}"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_DATABASE_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": _DB_HOST,
        "PORT": "5432",
        "OPTIONS": {
            "pool": {
                "min_size": 1,
                "max_size": 20,
            },
        },
    },
}
