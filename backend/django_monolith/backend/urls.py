"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from diagrams_assistant.auth_views import (
    LoginView,
    RegisterView,
    LogoutView,
    UserView,
    PasswordResetView,
    PasswordResetConfirmView,
    GoogleAuthURLView,
    GoogleLoginView,
    CustomTokenRefreshView,
)

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/v1/", include("diagrams_assistant.urls")),
    # Auth endpoints
    path("api/v1/auth/login/", LoginView.as_view(), name="login"),
    path("api/v1/auth/registration/", RegisterView.as_view(), name="register"),
    path("api/v1/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/v1/auth/user/", UserView.as_view(), name="user"),
    path(
        "api/v1/auth/password/reset/",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "api/v1/auth/password/reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "api/v1/auth/token/refresh/",
        CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/auth/social/google/url/",
        GoogleAuthURLView.as_view(),
        name="google_auth_url",
    ),
    path("api/v1/auth/social/google/", GoogleLoginView.as_view(), name="google_login"),
]
