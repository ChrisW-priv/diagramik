<div align="center">
    <img src="assets/Logo.png" alt="diagramik logo" width="180" />
    <h1>Diagramik</h1>
</div>

Diagramik is a diagram-as-code web application for software engineers and cloud
architects. You can describe what you want in natural language; an AI agent
generates the code that diagrams are rendered from. Diagrams can be easily
versioned, stored, organized and shared.

## Why use Diagramik?

Diagramik is an answer to a common problem for developers, product owners,
product menagers and any other role that requires transfer of complex ideas.
Ability to visually explain ideas and share them with others is sometimes
invaluable and can simplify pages of complex docs into simple visual tool
(Visual cortex is there for a reason; image is simple, symbols are complicated
🤓📚)

## Repository Structure

The project is organized as a monorepo with clear separation between the
frontend, backend, infrastructure, and supporting documentation:

| Directory         | Purpose                                                            |
| ----------------- | ------------------------------------------------------------------ |
| `frontend/`       | Astro 5 SSG web app (Vue 3, Tailwind CSS)                          |
| `backend/`        | Django REST API, MCP diagram server, Claude agent, cloud functions |
| `infrastructure/` | Terraform configuration for all GCP resources                      |
| `.github/`        | GitHub Actions CI/CD workflows                                     |
| `adl/`            | Architecture Decision Records                                      |

```
.
├── .github/            # CI/CD workflows
├── adl/                # Architecture Decision Records
├── backend/
│   ├── agent/          # Claude-based diagram generation agent
│   ├── cloud-functions/
│   ├── django_monolith/
│   ├── mcp_diagrams/   # MCP server exposing diagram tools
│   └── renderer/       # Diagram rendering service
├── frontend/
│   ├── public/
│   └── src/
└── infrastructure/
    ├── environments/
    ├── modules/
    └── main.tf
```

## Architecture

![Architecture Diagram](https://diagramik.com/share/cc323918-5e26-4102-9dc4-2c03152703b9)
