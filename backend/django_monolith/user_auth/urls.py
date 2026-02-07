from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    UserView,
    PasswordResetView,
    PasswordResetConfirmView,
    CustomTokenRefreshView,
    GoogleAuthURLView,
    GoogleLoginView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    SetNewPasswordView,
)
from user_auth.views.google_auth.complete_oauth import CompleteOAuthRegistrationView
from user_auth.views.google_auth.decode_state import DecodeOAuthStateView

urlpatterns = [
    # Email/Password Auth
    path("login/", LoginView.as_view(), name="auth-login"),
    path("registration/", RegisterView.as_view(), name="auth-register"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("user/", UserView.as_view(), name="auth-user"),
    path("password/reset/", PasswordResetView.as_view(), name="auth-password-reset"),
    path(
        "password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="auth-password-reset-confirm",
    ),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="auth-token-refresh"),
    # Email Verification
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="auth-resend-verification",
    ),
    # Password Reset (New System)
    path(
        "password-reset-request/",
        PasswordResetRequestView.as_view(),
        name="auth-password-reset-request",
    ),
    path(
        "set-new-password/", SetNewPasswordView.as_view(), name="auth-set-new-password"
    ),
    # Google OAuth
    path("social/google/url/", GoogleAuthURLView.as_view(), name="auth-google-url"),
    path("social/google/", GoogleLoginView.as_view(), name="auth-google-login"),
    path(
        "social/google/complete/",
        CompleteOAuthRegistrationView.as_view(),
        name="complete-oauth",
    ),
    path(
        "social/google/decode-state/",
        DecodeOAuthStateView.as_view(),
        name="decode-oauth-state",
    ),
]
