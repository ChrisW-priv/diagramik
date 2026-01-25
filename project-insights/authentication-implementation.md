# Authentication Implementation Report

**Date:** 2026-01-24
**Scope:** Google SSO, Email/Password Login, Logout, Password Reset

______________________________________________________________________

## Overview

Implemented JWT-based authentication with two login methods:

1. Email/Password (traditional)
1. Google SSO (OAuth 2.0)

Both methods result in the same outcome: a Django `User` record with JWT tokens for API access.

______________________________________________________________________

## Login Flow: Email + Password

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EMAIL/PASSWORD LOGIN FLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐                    ┌──────────────┐                ┌─────────┐
    │  Browser │                    │    Django    │                │   DB    │
    │ (Vue.js) │                    │   Backend    │                │         │
    └────┬─────┘                    └──────┬───────┘                └────┬────┘
         │                                 │                              │
         │  1. User enters email/password  │                              │
         │─────────────────────────────────>                              │
         │  POST /api/v1/auth/login/       │                              │
         │  {email, password}              │                              │
         │                                 │                              │
         │                                 │  2. Lookup user by email     │
         │                                 │─────────────────────────────>│
         │                                 │                              │
         │                                 │  3. Return User record       │
         │                                 │<─────────────────────────────│
         │                                 │                              │
         │                                 │  4. Verify password          │
         │                                 │  (check_password())          │
         │                                 │                              │
         │                                 │  5. Generate JWT tokens      │
         │                                 │  (RefreshToken.for_user())   │
         │                                 │                              │
         │  6. Return tokens + user data   │                              │
         │<─────────────────────────────────                              │
         │  {access, refresh, user}        │                              │
         │                                 │                              │
         │  7. Store in localStorage:      │                              │
         │     - diagramik_tokens          │                              │
         │     - diagramik_user            │                              │
         │                                 │                              │
         │  8. Redirect to /diagrams       │                              │
         │                                 │                              │
    ┌────┴─────┐                    ┌──────┴───────┐                ┌────┴────┐
    │  Browser │                    │    Django    │                │   DB    │
    └──────────┘                    └──────────────┘                └─────────┘


    SUBSEQUENT API REQUESTS:
    ────────────────────────
         │                                 │
         │  GET /api/v1/diagrams/          │
         │  Authorization: Bearer <access> │
         │─────────────────────────────────>
         │                                 │
         │                                 │  Decode JWT → user_id
         │                                 │  Fetch User from DB
         │                                 │
         │  Response with user's diagrams  │
         │<─────────────────────────────────
         │                                 │
```

______________________________________________________________________

## Login Flow: Google SSO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GOOGLE SSO LOGIN FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────────┐      ┌──────────┐      ┌─────────┐
    │  Browser │      │    Django    │      │  Google  │      │   DB    │
    │ (Vue.js) │      │   Backend    │      │  OAuth   │      │         │
    └────┬─────┘      └──────┬───────┘      └────┬─────┘      └────┬────┘
         │                   │                   │                  │
         │  1. User clicks   │                   │                  │
         │  "Continue with   │                   │                  │
         │   Google"         │                   │                  │
         │                   │                   │                  │
         │  2. GET /api/v1/auth/social/google/url/                  │
         │──────────────────>│                   │                  │
         │                   │                   │                  │
         │  3. Return OAuth URL                  │                  │
         │<──────────────────│                   │                  │
         │  {auth_url: "https://accounts.google.com/..."}          │
         │                   │                   │                  │
         │  4. Redirect to Google               │                  │
         │──────────────────────────────────────>│                  │
         │                   │                   │                  │
         │                   │   5. User logs in │                  │
         │                   │   with Google     │                  │
         │                   │   credentials     │                  │
         │                   │                   │                  │
         │  6. Redirect to /auth/google/callback?code=XXXXX        │
         │<──────────────────────────────────────│                  │
         │                   │                   │                  │
         │  7. POST /api/v1/auth/social/google/  │                  │
         │  {code: "XXXXX"}  │                   │                  │
         │──────────────────>│                   │                  │
         │                   │                   │                  │
         │                   │  8. Exchange code for tokens        │
         │                   │  POST oauth2.googleapis.com/token   │
         │                   │──────────────────>│                  │
         │                   │                   │                  │
         │                   │  9. Return access_token             │
         │                   │<──────────────────│                  │
         │                   │                   │                  │
         │                   │  10. GET /oauth2/v2/userinfo        │
         │                   │  Authorization: Bearer <token>      │
         │                   │──────────────────>│                  │
         │                   │                   │                  │
         │                   │  11. Return user info               │
         │                   │  {id, email, given_name, ...}       │
         │                   │<──────────────────│                  │
         │                   │                   │                  │
         │                   │  12. Find or create Django User     │
         │                   │  (see User Persistence below)       │
         │                   │─────────────────────────────────────>│
         │                   │                   │                  │
         │                   │  13. Generate JWT tokens            │
         │                   │  (RefreshToken.for_user())          │
         │                   │                   │                  │
         │  14. Return tokens + user data        │                  │
         │<──────────────────│                   │                  │
         │  {access, refresh, user}              │                  │
         │                   │                   │                  │
         │  15. Store in localStorage            │                  │
         │  16. Redirect to /diagrams            │                  │
         │                   │                   │                  │
    ┌────┴─────┐      ┌──────┴───────┐      ┌────┴─────┐      ┌────┴────┐
    │  Browser │      │    Django    │      │  Google  │      │   DB    │
    └──────────┘      └──────────────┘      └──────────┘      └─────────┘
```

______________________________________________________________________

## User Persistence: Django User ID vs Google SSO

### Database Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE TABLES                                │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐       ┌─────────────────────────────────────┐
│        auth_user            │       │     socialaccount_socialaccount     │
│  (Django's User model)      │       │        (from django-allauth)        │
├─────────────────────────────┤       ├─────────────────────────────────────┤
│  id (PK)          INTEGER   │←──┐   │  id (PK)              INTEGER       │
│  username         VARCHAR   │   │   │  user_id (FK)         INTEGER ──────┼──┐
│  email            VARCHAR   │   │   │  provider             VARCHAR       │  │
│  password         VARCHAR   │   │   │  uid                  VARCHAR       │  │
│  first_name       VARCHAR   │   │   │  extra_data           JSON          │  │
│  last_name        VARCHAR   │   │   │  last_login           DATETIME      │  │
│  is_active        BOOLEAN   │   │   └─────────────────────────────────────┘  │
│  date_joined      DATETIME  │   │                                            │
└─────────────────────────────┘   └────────────────────────────────────────────┘

Example data:
─────────────

auth_user:
┌────┬─────────────────────┬─────────────────────┬──────────────┬────────────┐
│ id │ username            │ email               │ password     │ first_name │
├────┼─────────────────────┼─────────────────────┼──────────────┼────────────┤
│  1 │ john@example.com    │ john@example.com    │ pbkdf2$...   │ John       │  ← Email signup
│  2 │ jane@gmail.com      │ jane@gmail.com      │ (unusable)   │ Jane       │  ← Google signup
│  3 │ bob@company.com     │ bob@company.com     │ pbkdf2$...   │ Bob        │  ← Email, linked Google
└────┴─────────────────────┴─────────────────────┴──────────────┴────────────┘

socialaccount_socialaccount:
┌────┬─────────┬──────────┬─────────────────────┬─────────────────────────────┐
│ id │ user_id │ provider │ uid                 │ extra_data                  │
├────┼─────────┼──────────┼─────────────────────┼─────────────────────────────┤
│  1 │    2    │ google   │ 117234567890123456  │ {"email": "jane@gmail.com"} │
│  2 │    3    │ google   │ 109876543210987654  │ {"email": "bob@company.com"}│
└────┴─────────┴──────────┴─────────────────────┴─────────────────────────────┘
```

### How User Lookup Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GOOGLE LOGIN USER LOOKUP LOGIC                           │
└─────────────────────────────────────────────────────────────────────────────┘

                              Google returns:
                              - google_id: "117234567890123456"
                              - email: "jane@gmail.com"
                              - given_name: "Jane"
                                        │
                                        ▼
                    ┌───────────────────────────────────────┐
                    │  1. Check SocialAccount table         │
                    │     WHERE provider='google'           │
                    │     AND uid=google_id                 │
                    └───────────────────────────────────────┘
                                        │
                        ┌───────────────┴───────────────┐
                        │                               │
                        ▼                               ▼
                    FOUND                           NOT FOUND
                        │                               │
                        ▼                               ▼
            ┌───────────────────────┐   ┌───────────────────────────────┐
            │ Return linked User    │   │ 2. Check User table           │
            │ (social_account.user) │   │    WHERE email=google_email   │
            └───────────────────────┘   └───────────────────────────────┘
                                                        │
                                        ┌───────────────┴───────────────┐
                                        │                               │
                                        ▼                               ▼
                                    FOUND                           NOT FOUND
                                        │                               │
                                        ▼                               ▼
                        ┌─────────────────────────┐   ┌───────────────────────────┐
                        │ Link existing User to   │   │ 3. Create new User        │
                        │ Google SocialAccount    │   │    username = email       │
                        │ (allows password +      │   │    email = google_email   │
                        │  Google login)          │   │    first_name = given_name│
                        └─────────────────────────┘   │    password = unusable    │
                                                      │                           │
                                                      │ 4. Create SocialAccount   │
                                                      │    linking User to Google │
                                                      └───────────────────────────┘
                                        │                               │
                                        └───────────────┬───────────────┘
                                                        │
                                                        ▼
                                        ┌───────────────────────────────┐
                                        │  Generate JWT for Django User │
                                        │  user_id is ALWAYS the        │
                                        │  Django auth_user.id          │
                                        └───────────────────────────────┘
```

### Key Points

1. **Single User Identity**: Whether logging in via email/password or Google, the user is always identified by their Django `auth_user.id`.

1. **JWT Contains Django User ID**: The JWT token's payload includes `user_id` which is the Django User's primary key:

   ```json
   {
     "user_id": 2,
     "exp": 1737844800,
     "iat": 1737841200,
     "jti": "abc123..."
   }
   ```

1. **SocialAccount Links Google ID to Django User**: The `socialaccount_socialaccount` table maps Google's UID to a Django User.

1. **Email Unification**: If a user signs up with email first, then later logs in with Google using the same email, the accounts are linked (same Django User).

1. **Password Handling**:

   - Email signup: Password is hashed and stored
   - Google-only signup: Password is set to unusable (`!` prefix)
   - Linked accounts: Can use either method

______________________________________________________________________

## API Endpoints

### Authentication Endpoints

| Endpoint                               | Method | Auth Required | Purpose                             |
| -------------------------------------- | ------ | ------------- | ----------------------------------- |
| `/api/v1/auth/login/`                  | POST   | No            | Email/password login                |
| `/api/v1/auth/registration/`           | POST   | No            | Register new user                   |
| `/api/v1/auth/logout/`                 | POST   | Yes           | Logout (blacklist refresh token)    |
| `/api/v1/auth/user/`                   | GET    | Yes           | Get current user info               |
| `/api/v1/auth/user/`                   | PATCH  | Yes           | Update user (first_name, last_name) |
| `/api/v1/auth/password/reset/`         | POST   | No            | Request password reset email        |
| `/api/v1/auth/password/reset/confirm/` | POST   | No            | Confirm reset with token            |
| `/api/v1/auth/token/refresh/`          | POST   | No            | Refresh access token                |
| `/api/v1/auth/social/google/url/`      | GET    | No            | Get Google OAuth URL                |
| `/api/v1/auth/social/google/`          | POST   | No            | Complete Google OAuth login         |

### Request/Response Examples

#### Login (Email/Password)

```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secretpassword"
}
```

Response (200 OK):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

#### Registration

```http
POST /api/v1/auth/registration/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password1": "securepassword123",
  "password2": "securepassword123",
  "first_name": "Jane"
}
```

Response (201 Created):

```json
{
  "detail": "Verification email sent. Please check your inbox."
}
```

#### Google OAuth - Get URL

```http
GET /api/v1/auth/social/google/url/
```

Response:

```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=xxx&redirect_uri=http://localhost:4321/auth/google/callback&response_type=code&scope=openid%20email%20profile"
}
```

#### Google OAuth - Exchange Code

```http
POST /api/v1/auth/social/google/
Content-Type: application/json

{
  "code": "4/0AX4XfWh..."
}
```

Response (200 OK):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "pk": 2,
    "email": "googleuser@gmail.com",
    "first_name": "Google",
    "last_name": "User"
  }
}
```

#### Token Refresh

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Response:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Password Reset Request

```http
POST /api/v1/auth/password/reset/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Response:

```json
{
  "detail": "Password reset email sent if account exists."
}
```

#### Password Reset Confirm

```http
POST /api/v1/auth/password/reset/confirm/
Content-Type: application/json

{
  "uid": "MQ",
  "token": "c5d4e3-a1b2c3d4e5f6...",
  "new_password1": "newsecurepassword",
  "new_password2": "newsecurepassword"
}
```

Response:

```json
{
  "detail": "Password reset successful."
}
```

______________________________________________________________________

## Files Modified/Created

### Backend

| File                                                              | Action   | Description             |
| ----------------------------------------------------------------- | -------- | ----------------------- |
| `backend/pyproject.toml`                                          | Modified | Added auth dependencies |
| `backend/django_monolith/backend/settings/auth_conf.py`           | Created  | Auth settings           |
| `backend/django_monolith/backend/settings/common_conf.py`         | Modified | Added apps, middleware  |
| `backend/django_monolith/backend/settings/rest_framework_conf.py` | Modified | JWT auth                |
| `backend/django_monolith/diagrams_assistant/auth_views.py`        | Created  | All auth views          |
| `backend/django_monolith/backend/urls.py`                         | Modified | Auth routes             |

### Frontend

| File                                                   | Action    | Description              |
| ------------------------------------------------------ | --------- | ------------------------ |
| `frontend/package.json`                                | Modified  | Added jwt-decode         |
| `frontend/src/lib/auth.ts`                             | Rewritten | JWT token management     |
| `frontend/src/lib/api.ts`                              | Rewritten | JWT interceptor, authApi |
| `frontend/src/components/LoginForm.vue`                | Rewritten | Email + Google login     |
| `frontend/src/components/RegisterForm.vue`             | Created   | Registration form        |
| `frontend/src/components/ForgotPasswordForm.vue`       | Created   | Password reset request   |
| `frontend/src/components/PasswordResetConfirmForm.vue` | Created   | Set new password         |
| `frontend/src/components/GoogleCallbackHandler.vue`    | Created   | OAuth callback           |
| `frontend/src/components/DiagramsList.vue`             | Modified  | New logout, user name    |
| `frontend/src/pages/auth/register.astro`               | Created   | Registration page        |
| `frontend/src/pages/auth/forgot-password.astro`        | Created   | Forgot password page     |
| `frontend/src/pages/auth/password-reset.astro`         | Created   | Reset confirmation page  |
| `frontend/src/pages/auth/google/callback.astro`        | Created   | Google callback page     |

______________________________________________________________________

## Environment Variables Required

```bash
# Google OAuth (from Google Cloud Console)
GOOGLE_OAUTH_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=xxx

DEFAULT_FROM_EMAIL=noreply@diagramik.com

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:4321  # dev
FRONTEND_URL=https://diagramik.com  # prod
```

______________________________________________________________________

## Note on Package Compatibility

The original plan specified `dj-rest-auth`, but it doesn't support Django 6.0. Custom auth views were implemented using `djangorestframework-simplejwt` directly, providing equivalent functionality.
