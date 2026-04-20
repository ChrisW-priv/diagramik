# Diagramik Backend — Structure Map

This document is the definitive reference for what lives where in this codebase. Read it before making changes or adding features.

## Tech Stack

- **Django 6** — REST API framework
- **Django REST Framework** — serializers, views, routers
- **PostgreSQL** (Cloud SQL) — primary database; SQLite in local dev
- **uv** — Python dependency management and virtual environments
- **pytest** — test runner with `pytest-django` and `pytest-cov`
- **ruff** — linting and formatting

## Service Inventory

| Service          | Directory                              | Cloud Run Name          | Purpose                                        |
| ---------------- | -------------------------------------- | ----------------------- | ---------------------------------------------- |
| Django API       | `django_monolith/`                     | `diagramik`             | REST API, auth, business logic                 |
| MCP Server       | `mcp_diagrams/`                        | `diagramik-mcp`         | Diagram generation (internal VPC only)         |
| Agent            | `agent/`                               | — (called by monolith)  | Claude AI agent for diagram prompts            |
| Share Function   | `cloud-functions/share-diagram-image/` | `share-diagram-image`   | Generates public share links                   |
| Render Function  | `cloud-functions/render-diagram/`      | `render-diagram`        | On-demand diagram rendering                    |
| Renderer Library | `renderer/`                            | — (uv workspace member) | Shared rendering utilities for cloud functions |

## Django Monolith — `django_monolith/`

Django project root is `django_monolith/`. The Django settings package is at `backend/settings/` (base) with `backend/deployed_settings/` overlays applied in production.

### Apps

| App                          | Owns                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `diagrams_assistant/`        | `Diagram`, `DiagramVersion`, `Workspace` models; diagram CRUD endpoints; AI agent invocation; share link generation |
| `user_auth/`                 | `User` model; registration, login, JWT auth, Google OAuth, email verification, password reset                       |
| `quota_management/`          | Per-user usage quotas; enforcement middleware                                                                       |
| `site_settings/`             | Runtime site configuration; admin-managed settings                                                                  |
| `django_emaillabs_sendmail/` | Email delivery via EmailLabs API                                                                                    |

### Settings

`DEPLOYMENT_ENVIRONMENT` env var selects the settings mode:

- `DEBUG` — local development (SQLite, relaxed security, no email)
- anything else — production settings loaded from `deployed_settings/` overlay

All secrets (DB credentials, GCS SA key, OAuth credentials, AI API key) are injected at runtime via GCP Secret Manager — they are never in config files.

### API Contract

`openapi-schema.yml` at the backend root is the source of truth for the API surface. The frontend `api.ts` is generated from this contract. Update it when adding or changing endpoints.

## Agent — `agent/`

DSPy-based multi-agent system that processes natural language diagram requests.

| Module    | Purpose                                                         |
| --------- | --------------------------------------------------------------- |
| `src/`    | Agent source code                                               |
| `skills/` | DSPy compiled programs (`.json`) — output of `t agent:optimize` |
| `tests/`  | Unit and integration tests                                      |
| `config/` | Agent configuration                                             |

Sub-agents: **router** (classifies request type), **technical** (infrastructure diagrams), **mermaid** (general Mermaid DSL), **fallback** (catch-all). The router dispatches to the appropriate sub-agent based on the user's prompt.

Run `t agent:optimize` to recompile DSPy modules after changing prompts or examples.

## Key Patterns

- The monolith calls the MCP service over VPC private networking. The MCP service URL is injected via the `MCP_SERVICE_URL` environment variable.
- Docker images use GHCR (`ghcr.io/...`) for cache and GAR (`europe-west4-docker.pkg.dev/...`) for production deployment.
- All tests use `pytest`; run with coverage via `t monolith:test` or `t mcp:test`.
- `ruff` handles both linting and formatting. Run `t fmt` to auto-fix.
