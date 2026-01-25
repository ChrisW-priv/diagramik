# Base builder
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:fcb50226f56cc30eb2d9fab234e1d15c2f26103b84b15d6e39ba75ed17c71876 AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --group django-monolith

FROM python:3.13-slim AS release

WORKDIR /app
COPY --from=base /app/.venv /app/.venv

COPY django_monolith/ /app/django_monolith/
RUN chmod +x /app/django_monolith/entrypoint.sh

COPY django_monolith/backend/deployed_settings/ /app/django_monolith/backend/settings/

CMD ["/app/django_monolith/entrypoint.sh", "run_asgi"]
