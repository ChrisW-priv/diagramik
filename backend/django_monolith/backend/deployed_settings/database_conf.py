import os


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_DATABASE_NAME = os.getenv("POSTGRES_DATABASE_NAME", "postgres")

db_conn_name = os.getenv("DB_CONN_NAME")
pre_db_conn_name = os.getenv("PRE_DB_CONN_NAME", "/cloudsql/")
unix_socket_path = f"{pre_db_conn_name}{db_conn_name}"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_DATABASE_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": unix_socket_path,
        "PORT": "5432",
        "OPTIONS": {
            "pool": {
                "min_size": 1,
                "max_size": 20,
            },
        },
    },
}
