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
)

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
    # Google OAuth
    path("social/google/url/", GoogleAuthURLView.as_view(), name="auth-google-url"),
    path("social/google/", GoogleLoginView.as_view(), name="auth-google-login"),
]
