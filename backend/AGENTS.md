## Commands

Tasks are defined in `Taskfile.yml` and run via `go-task` (aliased `t`). Dependencies are managed with `uv`; the virtualenv lives at `.venv/`.

```
t sync                  # Install all Python deps via uv
t monolith:dev          # Run Django dev server on :8000
t monolith:test         # Run pytest with coverage in django_monolith/
t monolith:check        # Validate Django settings
t monolith:check-prod   # Validate production Django settings
t mcp:dev               # Run MCP diagram server on :8080
t mcp:test              # Run MCP pytest suite
t agent:test            # Run agent unit tests
t build                 # Build all Docker images (monolith + mcp)
```

To run a single test file: `.venv/bin/pytest path/to/test.py`

The Django dev server requires `DEPLOYMENT_ENVIRONMENT=DEBUG` (set automatically by `t monolith:dev`).

## Services

- **`django_monolith/`** — REST API (Django 6, DRF). Apps: `diagrams_assistant`, `user_auth`, `quota_management`, `site_settings`, `django_emaillabs_sendmail`. API contract in `openapi-schema.yml`.
- **`mcp_diagrams/`** — MCP server for diagram generation. Converts Mermaid DSL to SVG/PNG via `mmdc` and stores output to GCS. Internal-only service (no public ingress).
- **`agent/`** — Claude AI agent built with DSPy. Sub-agents: router, technical, mermaid, fallback. Compile optimized agent programs via `t agent:optimize`.
- **`cloud-functions/`** — Two GCP Cloud Run functions: `share-diagram-image` (generates public share links), `render-diagram` (on-demand rendering). Both use the `renderer/` library.
- **`renderer/`** — Shared Python library (uv workspace member) used by the cloud functions.

Two Docker images are deployed to Cloud Run: `application-monolith` and `diagramming-mcp`. The MCP service is VPC-internal; the monolith calls it over private networking.

## Structure Map

Before making changes or adding features, read `README.md`. It is the definitive map of every Django app, its models and endpoints, the agent module layout, and how services connect.
