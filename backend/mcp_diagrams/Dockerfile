# Base builder
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim@sha256:fcb50226f56cc30eb2d9fab234e1d15c2f26103b84b15d6e39ba75ed17c71876 AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY agent/ /app/agent/
COPY renderer/ /app/renderer/
RUN uv sync --group diagram-mcp

# Release
FROM python:3.13-slim AS release

WORKDIR /app

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        graphviz \
        nodejs \
        npm \
        chromium \
    && npm install -g @mermaid-js/mermaid-cli \
    && rm -rf /var/lib/apt/lists/* \
    && echo '{"args":["--no-sandbox","--disable-dev-shm-usage"]}' > /app/puppeteer-config.json

COPY --from=base /app/.venv ./.venv
COPY --from=base /app/renderer /app/renderer
COPY mcp_diagrams ./

# Set the default command
CMD ["python", "/app/server.py"]
