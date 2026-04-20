Diagramik is a diagram-as-code web application. Users describe diagrams in
natural language, AI agent rewrites the request into code, then renders it and
displays the preview.

## Directory Guide

Each directory has its own AGENTS.md with commands, constraints, and a pointer
to a README.md structure map.

| Directory         | Contents                                  | Agent File                                             |
| ----------------- | ----------------------------------------- | ------------------------------------------------------ |
| `frontend/`       | Astro 5 SSG + Vue 3 web app               | [`frontend/AGENTS.md`](frontend/AGENTS.md)             |
| `backend/`        | Django REST API, MCP server, Claude agent | [`backend/AGENTS.md`](backend/AGENTS.md)               |
| `infrastructure/` | Terraform GCP configuration               | [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md) |
| `.github/`        | GitHub Actions CI/CD workflows            | [`.github/AGENTS.md`](.github/AGENTS.md)               |

Agent files have also been aliased to `CLAUDE.md` in each directory.

## Architecture Decisions (`adl/`)

An `adl/` directory contains Architecture Decision Records. Each file documents
a key design or platform decision with its rationale. On each feature addition
and change, try to find the original decision or create a new ADR, using the
`/log-adr` skill.
