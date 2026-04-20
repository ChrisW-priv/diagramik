# Diagramik Frontend — Structure Map

This document is the definitive reference for what lives where in this codebase.
Read it before making changes or adding features.

## Tech Stack

- **Astro 5** — routing, SSG, page shells
- **Vue 3** — all interactive UI components (hydrated client-side via `client:load`)
- **Tailwind CSS 3** — styling; design tokens in `tailwind.config.mjs`
- **TypeScript** — strict mode throughout
- **Heroicons v2** — icons (outline style only)
- No external component library

## Routing — `src/pages/`

| Route                        | File                              | Purpose                                                      |
| ---------------------------- | --------------------------------- | ------------------------------------------------------------ |
| `/`                          | `index.astro`                     | Auth check; redirects to `/diagrams` or `/login`             |
| `/login`                     | `login.astro`                     | Login page shell                                             |
| `/diagrams`                  | `diagrams/index.astro`            | Main app — sidebar (diagram list) + editor panel in one page |
| `/settings`                  | `settings.astro`                  | User account settings                                        |
| `/terms`                     | `terms.astro`                     | Terms of service                                             |
| `/auth/register`             | `auth/register.astro`             | Registration page shell                                      |
| `/auth/login`                | `auth/login.astro`                | Auth-scoped login page                                       |
| `/auth/forgot-password`      | `auth/forgot-password.astro`      | Password reset request                                       |
| `/auth/verification-pending` | `auth/verification-pending.astro` | Post-register verify prompt                                  |
| `/auth/verify-email`         | `auth/verify-email.astro`         | Email verification token handler                             |
| `/auth/password-reset`       | `auth/password-reset.astro`       | Reset password via email link                                |
| `/auth/set-new-password`     | `auth/set-new-password.astro`     | Change password (authenticated)                              |
| `/auth/google/callback`      | `auth/google/callback.astro`      | Google OAuth callback handler                                |

## Layout — `src/layouts/`

- **`Layout.astro`** — site-wide HTML shell; All pages use this layout.

## Components — `src/components/`

### Core App

| Component             | Purpose                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| `DiagramsPage.vue`    | Root app component mounted on `/diagrams`; owns diagram list state, sidebar toggle, and selected diagram |
| `DiagramsSidebar.vue` | Left panel; lists workspaces and diagrams, handles rename/delete/move, search                            |
| `DiagramView.vue`     | Right panel; tab container switching between Work and Display tabs                                       |
| `WorkTab.vue`         | AI chat interface; sends prompts, streams responses, shows version history                               |
| `DisplayTab.vue`      | Renders the diagram image/SVG for the selected version                                                   |
| `SettingsPage.vue`    | Account settings UI (name, password change, account deletion)                                            |

### Auth Forms

| Component                      | Purpose                                                   |
| ------------------------------ | --------------------------------------------------------- |
| `LoginForm.vue`                | Email/password login + Google OAuth entry point           |
| `RegisterForm.vue`             | Registration with name, email, password, terms acceptance |
| `ForgotPasswordForm.vue`       | Request password reset by email                           |
| `PasswordResetConfirmForm.vue` | Confirm reset via uid+token from email link               |
| `SetNewPasswordForm.vue`       | Set new password (authenticated or via reset token)       |
| `GoogleCallbackHandler.vue`    | Handles OAuth code exchange after Google redirect         |
| `EmailVerificationHandler.vue` | Processes email verification token from URL               |
| `VerificationPendingView.vue`  | Prompts user to check their inbox; resend option          |

### Base / Reusable

| Component                | Purpose                                          |
| ------------------------ | ------------------------------------------------ |
| `base/AlertError.vue`    | Red error alert banner                           |
| `base/AlertSuccess.vue`  | Green success alert banner                       |
| `base/AlertWarning.vue`  | Yellow warning alert banner                      |
| `base/FormContainer.vue` | Centered card wrapper for auth forms             |
| `base/FormField.vue`     | Labeled input field with validation message slot |
| `base/GoogleLogo.vue`    | SVG Google logo used in OAuth buttons            |

## Libraries — `src/lib/`

### `api.ts`

Axios client (`apiClient`) with base URL `{API_BASE}/api/v1`. All application code must use `apiClient` (not bare `axios`) so request/response interceptors run.

- **Request interceptor**: attaches `Authorization: Bearer <token>`; auto-refreshes expired access token using refresh token before retrying
- **Response interceptor**: on 401, clears tokens and redirects to `/login`
- Exports typed functions for all endpoints: `getDiagrams`, `getDiagram`, `createDiagram`, `createDiagramVersion`, `deleteDiagram`, `deleteDiagramVersion`, `updateDiagram`, `updateDiagramWorkspace`, `getWorkspaces`, `createWorkspace`, `updateWorkspace`, `deleteWorkspace`, `createShareLink`
- Exports `authApi` object with methods: `login`, `register`, `logout`, `getUser`, `updateUser`, `requestPasswordReset`, `confirmPasswordReset`, `getGoogleAuthUrl`, `googleLogin`, `completeOAuthRegistration`, `deleteAccount`, `refreshToken`, `verifyEmail`, `resendVerification`, `setNewPassword`

### `auth.ts`

Token and user state stored in `localStorage` under key `diagramik_auth`. Exports: `getStoredTokens`, `setTokens`, `clearTokens`, `isTokenExpired`, `getAuthHeader`, `getStoredUser`, `setUser`.

### `config.ts`

Single source of truth for all constants. Always add new magic numbers here instead of inlining. Namespaces: `CONFIG.API`, `CONFIG.OAUTH`, `CONFIG.AUTH`, `CONFIG.VALIDATION`, `CONFIG.UI`, `CONFIG.TIMERS`.

## Design System

See `.impeccable.md` for the full design specification including color tokens, brand personality, and UI principles.

**Color roles** (Tailwind classes):

- Page background: `gray-900` | Surface/card: `gray-800` | Input/hover: `gray-700`
- Border: `gray-600` | Muted text: `gray-400` | Label: `gray-300` | Primary text: `white`
- Primary action: `blue-600` | Link/accent: `blue-400`
- Error: `red-400`/`red-500` | Success: `green-400`/`green-500` | Warning: `yellow-400`/`yellow-500`

## Key Patterns

- Astro pages are static shells; all interactivity lives in Vue components mounted with `client:load`
- API base URL is environment-switched in `config.ts`: prod → `https://diagramik.com`, dev → `http://localhost:8000`
- Auth tokens are JWT; access token is short-lived, refresh token triggers silent re-auth
- All new constants belong in `CONFIG` in `config.ts`
- Icons: always use Heroicons v2 outline variants from `@heroicons/vue/24/outline`
