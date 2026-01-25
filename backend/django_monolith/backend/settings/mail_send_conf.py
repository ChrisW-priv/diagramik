import os

EMAIL_BACKEND = "django_emaillabs_sendmail.backend.EmailLabsEmailBackend"


EMAILLABS_API_URL = "https://api.emaillabs.net.pl/api/new_sendmail"
EMAILLABS_API_SMTP_ACCOUNT_NAME = "1.chriswatras.smtp"
EMAILLABS_API_APP_KEY = os.getenv("EMAILLABS_API_APP_KEY")
EMAILLABS_API_SECRET_KEY = os.getenv("EMAILLABS_API_SECRET_KEY")
EMAIL_APP_DISPLAY_NAME = "Diagramik"

DEFAULT_FROM_EMAIL = "noreply@diagramik.com"
