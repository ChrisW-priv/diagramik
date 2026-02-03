from .email_password_auth import (
    LoginView,
    RegisterView,
    LogoutView,
    UserView,
    PasswordResetView,
    PasswordResetConfirmView,
    CustomTokenRefreshView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    SetNewPasswordView,
)
from .google_auth import (
    GoogleAuthURLView,
    GoogleLoginView,
)

__all__ = [
    # Email/Password Auth
    "LoginView",
    "RegisterView",
    "LogoutView",
    "UserView",
    "PasswordResetView",
    "PasswordResetConfirmView",
    "CustomTokenRefreshView",
    # Email Verification
    "VerifyEmailView",
    "ResendVerificationEmailView",
    # Password Reset (New System)
    "PasswordResetRequestView",
    "SetNewPasswordView",
    # Google OAuth
    "GoogleAuthURLView",
    "GoogleLoginView",
]
