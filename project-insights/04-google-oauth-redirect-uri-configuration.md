# Google OAuth Redirect URI Configuration

**Date:** 2026-01-30
**Issue:** `redirect_uri_mismatch` error during Google SSO login
**Resolution:** Updated backend to use backend URL as OAuth callback instead of frontend URL

______________________________________________________________________

## Problem

The Google OAuth flow was failing with `redirect_uri_mismatch` error. The Google Cloud Console was configured with:

```
https://diagramik.com/api/v1/auth/social/google/
```

But the backend was sending:

```
https://diagramik.com/auth/google/callback
```

This mismatch caused Google to reject the OAuth request.

______________________________________________________________________

## Solution Overview

Changed the OAuth flow to redirect to the **backend** for OAuth callback handling, rather than the frontend. The backend now:

1. Receives the OAuth callback from Google
1. Exchanges the authorization code for tokens
1. Creates/logs in the user
1. Redirects to the frontend with JWT tokens in query parameters

______________________________________________________________________

## Implementation Details

### 1. Backend Configuration (`backend/django_monolith/backend/settings/__init__.py`)

Added `BACKEND_URL` setting for OAuth callbacks:

```python
# Backend URL for OAuth callbacks
DEFAULT_BACKEND_URL = "http://localhost:8000" if DEBUG else "https://diagramik.com"
BACKEND_URL = os.environ.get("BACKEND_URL", DEFAULT_BACKEND_URL)
```

**Environment Variables:**

- `BACKEND_URL` (optional): Override the default backend URL
- Defaults to `http://localhost:8000` in DEBUG mode
- Defaults to `https://diagramik.com` in production

### 2. Updated GoogleAuthURLView (`auth_views.py:312`)

Changed the OAuth redirect URI from frontend to backend:

```python
def get(self, request):
    client_id = settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"]
    callback_url = f"{settings.BACKEND_URL}/api/v1/auth/social/google/"  # Backend callback
    oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={callback_url}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile"
    )
    return Response({"auth_url": oauth_url})
```

### 3. Added GET Handler to GoogleLoginView (`auth_views.py:328`)

The backend now handles Google's OAuth callback redirect with a GET method:

```python
def get(self, request):
    """Handle Google OAuth callback redirect"""
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return redirect(f"{settings.FRONTEND_URL}/?error={error}")

    if not code:
        return redirect(f"{settings.FRONTEND_URL}/?error=no_code")

    try:
        # Exchange code for tokens
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["client_id"],
                "client_secret": settings.SOCIALACCOUNT_PROVIDERS["google"]["APP"]["secret"],
                "redirect_uri": f"{settings.BACKEND_URL}/api/v1/auth/social/google/",
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            return redirect(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # Get user info from Google
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # ... (user creation/lookup logic) ...

        jwt_tokens = get_tokens_for_user(user)

        # Redirect to frontend with JWT tokens
        from urllib.parse import urlencode
        params = urlencode({
            "access": jwt_tokens["access"],
            "refresh": jwt_tokens["refresh"],
        })
        return redirect(f"{settings.FRONTEND_URL}/auth/google/callback?{params}")

    except Exception:
        return redirect(f"{settings.FRONTEND_URL}/?error=auth_failed")
```

### 4. Updated Frontend GoogleCallbackHandler (`frontend/src/components/GoogleCallbackHandler.vue`)

Simplified to extract JWT tokens directly from query parameters:

```typescript
onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get('access');
  const refreshToken = urlParams.get('refresh');
  const errorParam = urlParams.get('error');

  if (errorParam) {
    error.value = 'Google sign-in was cancelled or failed.';
    loading.value = false;
    return;
  }

  if (!accessToken || !refreshToken) {
    error.value = 'No tokens received from authentication server.';
    loading.value = false;
    return;
  }

  try {
    // Store tokens
    setTokens({ access: accessToken, refresh: refreshToken });

    // Redirect to diagrams page
    window.location.href = '/diagrams';
  } catch (err: any) {
    error.value = 'Failed to complete Google sign-in. Please try again.';
    loading.value = false;
  }
});
```

______________________________________________________________________

## OAuth Flow (Updated)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOOGLE SSO LOGIN FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────┐           ┌──────────┐           ┌────────┐           ┌──────────┐
│ Browser  │           │  Django  │           │ Google │           │ Frontend │
│ (Vue.js) │           │ Backend  │           │  OAuth │           │ (Astro)  │
└────┬─────┘           └────┬─────┘           └───┬────┘           └────┬─────┘
     │                      │                     │                      │
     │ 1. Click "Sign in    │                     │                      │
     │    with Google"      │                     │                      │
     │                      │                     │                      │
     │ 2. GET /api/v1/auth/social/google/url/     │                      │
     │─────────────────────>│                     │                      │
     │                      │                     │                      │
     │ 3. Return OAuth URL  │                     │                      │
     │    (redirect_uri=    │                     │                      │
     │    backend/api/v1/   │                     │                      │
     │    auth/social/      │                     │                      │
     │    google/)          │                     │                      │
     │<─────────────────────│                     │                      │
     │                      │                     │                      │
     │ 4. Redirect to Google OAuth                │                      │
     │────────────────────────────────────────────>                      │
     │                      │                     │                      │
     │ 5. User authenticates│                     │                      │
     │    & grants consent  │                     │                      │
     │                      │                     │                      │
     │ 6. Google redirects to backend with code   │                      │
     │    GET /api/v1/auth/social/google/?code=XXX│                      │
     │────────────────────────────────────────────>                      │
     │                      │                     │                      │
     │                      │ 7. Exchange code    │                      │
     │                      │    for tokens       │                      │
     │                      │────────────────────>│                      │
     │                      │                     │                      │
     │                      │ 8. Return Google    │                      │
     │                      │    access token     │                      │
     │                      │<────────────────────│                      │
     │                      │                     │                      │
     │                      │ 9. Get user info    │                      │
     │                      │────────────────────>│                      │
     │                      │                     │                      │
     │                      │ 10. Return user     │                      │
     │                      │     profile         │                      │
     │                      │<────────────────────│                      │
     │                      │                     │                      │
     │                      │ 11. Create/lookup   │                      │
     │                      │     Django user     │                      │
     │                      │                     │                      │
     │                      │ 12. Generate JWT    │                      │
     │                      │     tokens          │                      │
     │                      │                     │                      │
     │ 13. Redirect to frontend with JWT tokens   │                      │
     │    /auth/google/callback?access=XXX&refresh=YYY                   │
     │───────────────────────────────────────────────────────────────────>
     │                      │                     │                      │
     │                      │                     │         14. Extract  │
     │                      │                     │         tokens from  │
     │                      │                     │         query params │
     │                      │                     │                      │
     │                      │                     │         15. Store in │
     │                      │                     │         localStorage │
     │                      │                     │                      │
     │ 16. Redirect to /diagrams                  │                      │
     │<───────────────────────────────────────────────────────────────────
     │                      │                     │                      │
```

______________________________________________________________________

## Google Cloud Console Configuration

### Required Redirect URIs

You must configure these **exact** redirect URIs in Google Cloud Console:

**Production:**

```
https://diagramik.com/api/v1/auth/social/google/
```

**Development:**

```
http://localhost:8000/api/v1/auth/social/google/
```

### Important Notes

1. **Backend URLs only**: Only the backend URLs need to be registered with Google
1. **Frontend URLs are internal**: The frontend callback (`/auth/google/callback`) is an internal redirect from the backend
1. **No trailing slash**: The URIs must match exactly (Google is case-sensitive)
1. **Protocol matters**: Use `https://` for production, `http://` for localhost
1. **Port required for localhost**: Include `:8000` for local development

### Setup Steps

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
1. Select your OAuth 2.0 Client ID
1. Under "Authorized redirect URIs", add both production and development URLs
1. Click "Save"
1. Wait 5 minutes for changes to propagate

______________________________________________________________________

## Environment Variables

### Backend Required Variables

```bash
# Google OAuth credentials
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# URLs (optional - have defaults)
BACKEND_URL=https://diagramik.com          # Production backend
FRONTEND_URL=https://diagramik.com         # Production frontend

# For local development
BACKEND_URL=http://localhost:8000          # Dev backend
FRONTEND_URL=http://localhost:4321         # Dev frontend
```

### Frontend Configuration

The frontend automatically detects the environment:

- **Dev mode**: Points to `http://localhost:8000`
- **Production**: Points to `https://diagramik.com`

No additional configuration needed.

______________________________________________________________________

## Security Considerations

### What's Secure

✅ **Client Secret never exposed to frontend**: Only used server-side for token exchange
✅ **Authorization Code Flow**: Uses the most secure OAuth 2.0 flow
✅ **JWT tokens**: Short-lived access tokens with refresh mechanism
✅ **Backend validation**: All OAuth responses validated server-side
✅ **Error handling**: User-friendly error messages, technical details hidden

### Potential Improvements

⚠️ **Consider httpOnly cookies**: Currently using localStorage for JWT tokens, which is vulnerable to XSS attacks. Consider using httpOnly cookies for extra security.

⚠️ **Add PKCE**: The flow doesn't use PKCE (Proof Key for Code Exchange), which is recommended for public clients to prevent authorization code interception attacks.

⚠️ **Rate limiting**: Add rate limiting to OAuth endpoints to prevent abuse.

______________________________________________________________________

## Troubleshooting

### Common Issues

1. **redirect_uri_mismatch error**

   - Check that Google Console redirect URI exactly matches `{BACKEND_URL}/api/v1/auth/social/google/`
   - Verify no trailing slash
   - Ensure protocol matches (http vs https)

1. **token_exchange_failed error**

   - Verify `GOOGLE_OAUTH_CLIENT_SECRET` is set correctly
   - Check that authorization code hasn't expired (codes expire in ~10 minutes)
   - Ensure redirect_uri in token exchange matches the one used for authorization

1. **Tokens not being stored**

   - Check browser console for localStorage errors
   - Verify frontend callback handler is receiving tokens in query params
   - Check for CORS issues between backend and frontend

1. **User not being created**

   - Check backend logs for database errors
   - Verify Google user info includes email
   - Check if user already exists with different auth method

______________________________________________________________________

## Files Modified

### Backend

- `backend/django_monolith/backend/settings/__init__.py` - Added `BACKEND_URL` configuration
- `backend/django_monolith/diagrams_assistant/auth_views.py` - Updated OAuth flow to use backend redirect

### Frontend

- `frontend/src/components/GoogleCallbackHandler.vue` - Simplified to extract tokens from query params

______________________________________________________________________

## Testing

### Local Development Testing

1. Set environment variables:

```bash
export GOOGLE_OAUTH_CLIENT_ID="your-client-id"
export GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
export BACKEND_URL="http://localhost:8000"
export FRONTEND_URL="http://localhost:4321"
```

2. Start backend:

```bash
task be:monolith:dev
```

3. Start frontend:

```bash
task fe:dev
```

4. Open browser to `http://localhost:4321/login`
1. Click "Continue with Google"
1. Should redirect to Google OAuth consent screen
1. After granting consent, should redirect back to `http://localhost:4321/auth/google/callback?access=...&refresh=...`
1. Should store tokens and redirect to `/diagrams`

### Production Testing

1. Verify environment variables are set in Cloud Run
1. Test OAuth flow at `https://diagramik.com/login`
1. Monitor Cloud Run logs for any errors
1. Check that users are being created in database

______________________________________________________________________

## Related Documentation

- [Authentication Implementation Report](./authentication-implementation.md) - Full authentication system documentation
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
