import os
from datetime import timedelta

# Authentication backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True

# Google OAuth
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "APP": {
            "client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
            "secret": os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", ""),
        },
    }
}
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# SimpleJWT settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Email Verification Configuration
EMAIL_VERIFICATION_MAX_RESENDS = 5  # Maximum number of resend attempts
EMAIL_VERIFICATION_COOLDOWN_MINUTES = 10  # Cooldown period between resends in minutes
EMAIL_VERIFICATION_TOKEN_EXPIRY_DAYS = 1  # Email verification tokens expire after 1 day

# Password Reset Configuration
PASSWORD_RESET_MAX_REQUESTS = 5  # Maximum password reset requests per cooldown period
PASSWORD_RESET_COOLDOWN_MINUTES = 10  # Cooldown period between password reset requests
PASSWORD_RESET_TOKEN_EXPIRY_DAYS = 1  # Password reset tokens expire after 1 day
PASSWORD_RESET_TIMEOUT = (
    86400  # Django default - 1 day in seconds (override default 3 days)
)
