import base64
import itertools
from typing import Iterable

import requests as rq
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMessage
from django.conf import settings


class EmailLabsEmailBackend(BaseEmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = EmailLabsClient(
            settings.EMAILLABS_API_URL,
            settings.EMAILLABS_API_SMTP_ACCOUNT_NAME,
            settings.EMAILLABS_API_APP_KEY,
            settings.EMAILLABS_API_SECRET_KEY,
            settings.EMAIL_APP_DISPLAY_NAME,
        )

    def send_messages(self, email_messages: list[EmailMessage]) -> int:
        nested_message = map(adapt_django_message_to_emaillabs, email_messages)
        message_requests = itertools.chain.from_iterable(nested_message)
        return sum(map(self._send_message, message_requests))

    def _send_message(self, email_params: dict) -> bool:
        response = self.client.send_mail(email_params)
        return response.ok


class EmailLabsClient:
    def __init__(self, url, smtp_account, app_key, secret_key, app_name) -> None:
        self.url = url
        self.smtp_account = smtp_account
        self.app_key = app_key
        self.secret_key = secret_key
        self.app_name = app_name

    @property
    def auth_token(self) -> str:
        secret_str = f"{self.app_key}:{self.secret_key}"
        secret_str_byte_encoded = secret_str.encode()
        secret_str_as_b64 = base64.b64encode(secret_str_byte_encoded)
        return secret_str_as_b64.decode()

    def send_mail(self, email_params: dict) -> rq.Response:
        default = {
            "smtp_account": self.smtp_account,
            "from_name": self.app_name,
        }
        email_dict = {**default, **email_params}
        return rq.post(
            self.url,
            headers={"Authorization": f"Basic {self.auth_token}"},
            data=email_dict,
        )


def adapt_django_message_to_emaillabs(email_message: EmailMessage) -> Iterable[dict]:
    return (
        {
            "from": email_message.from_email,
            "subject": email_message.subject,
            f"to[{to}]": "",
            "html": email_message.body,
        }
        for to in email_message.to or []
    )
