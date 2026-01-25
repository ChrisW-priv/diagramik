# Base builder
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:fcb50226f56cc30eb2d9fab234e1d15c2f26103b84b15d6e39ba75ed17c71876 AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --group diagram-mcp

# Release
FROM python:3.13-slim AS release

WORKDIR /app

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends graphviz && \
    rm -rf /var/lib/apt/lists/*

COPY --from=base /app/.venv ./.venv
COPY mcp_diagrams ./

# Set the default command
CMD ["python", "/app/server.py"]
