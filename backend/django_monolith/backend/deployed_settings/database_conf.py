import os


DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_DATABASE_NAME = os.getenv("POSTGRES_DATABASE_NAME", "postgres")

# Private IP only - public access disabled for security
DB_PRIVATE_IP = os.getenv("DB_PRIVATE_IP")

if not DB_PRIVATE_IP:
    raise ValueError("DB_PRIVATE_IP must be set - private VPC connection required")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_DATABASE_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_PRIVATE_IP,
        "PORT": "5432",
        "OPTIONS": {
            "pool": {
                "min_size": 1,
                "max_size": 20,
            },
        },
    },
}
