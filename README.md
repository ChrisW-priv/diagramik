<div align="center">
  <img src="assets/Logo.png" alt="diagramik logo" width="180" />

  <h1>diagramik</h1>

  <p><strong>Turn a plain description into a polished diagram.</strong></p>
</div>

---

## What is diagramik?

**diagramik** is an agentic AI application that converts plain-English descriptions into clean, exportable diagrams.

You describe what you want. The AI agent classifies your intent, selects the right diagram type, constructs the rendering call, and returns an image — no tooling knowledge required. The architecture also exposes a programmatic interface for users who want to integrate the agent layer directly into their own workflows.

**diagramik** is also a personal portfolio project — demonstrating what a production-ready AI system looks like end-to-end: secure cloud infrastructure, agentic AI with structured optimization, and a CI/CD pipeline that enforces quality at every step.

---

## User Flow

1. **Sign in** — via Google OAuth or email/password
2. **Describe your diagram** — in a chat interface, as you would to a colleague
3. **Get an image** — the AI agent selects the right diagram type and renders it
4. **Edit with history** — modify diagrams iteratively with full version history
5. **Save or share** — download the image or reference it with a share link

<!-- TODO: add screenshot -->

---

## Technical Architecture

The architecture is deliberately layered. Each concern lives in its own well-defined boundary — making the system easy to reason about, extend, and secure.

### Cloud Infrastructure (GCP + Terraform)

Production runs on **Google Cloud Platform**, fully defined with Terraform — no manual steps in the deployment pipeline.

<!-- TODO: add architecture diagram -->

**Key components:**

- **VPC Network** — private VPC (`10.0.0.0/24`) isolates all internal services from the public internet
- **Global Load Balancer** — single entry point for all traffic; path-based routing with CDN for the static frontend
- **Cloud Router + NAT** — internal services can reach external APIs (e.g., LLM providers) without exposing a public IP
- **Django Monolith** — REST API on Cloud Run; handles authentication, data models, quota enforcement, and agent orchestration. The **only** service with public ingress.
- **MCP Service** — diagram rendering on a second Cloud Run instance; accessible only over the internal VPC. No public ingress. All calls are service-to-service authenticated.
- **Cloud SQL** — PostgreSQL with **private IP only**; no public endpoint
- **GCS Bucket** — rendered images served via signed URLs; no public bucket ACLs

**Security posture:** The attack surface is minimal by design. Only the load balancer and the Django API are publicly reachable. All other services operate inside the VPC with no public ingress, and inter-service calls use GCP IAM-based authentication.

---

### CI/CD and Code Quality

The project follows **GitHub Flow**: feature branches, pull requests to `main`, and GitHub Releases that trigger the full production deployment.

#### Release Pipeline

On each new release tag, the pipeline:

1. Builds Docker images for all backend services
2. Pushes to GitHub Container Registry and Google Artifact Registry
3. Runs `terraform apply` — infrastructure changes are resolved automatically
4. Builds the Astro frontend (SSG) and publishes to GCS

One release tag. One pipeline run. Everything is live.

<!-- TODO: add pipeline diagram -->

#### Pre-commit Hooks

Code quality is enforced locally before anything reaches CI. The pre-commit configuration covers:

| Hook | What it enforces |
|---|---|
| `ruff` + `ruff-format` | Python linting and formatting |
| `actionlint` | GitHub Actions workflow correctness |
| `yamlfmt` | YAML formatting |
| `mdformat` | Markdown consistency |
| `terraform fmt` + `terraform validate` | Terraform syntax and schema validation |
| `gitleaks` + `talisman` | Secret scanning — blocks credential leaks at commit time |
| Backend tests + static checks | Run on pre-push via `task be:test` and `task check` |

Secret scanning (gitleaks + talisman) runs on every commit — credentials cannot be pushed accidentally. Container vulnerability scanning with **Trivy** is planned for the CI pipeline.

---

### Agentic AI Architecture

One of the most deliberate decisions in this project is the **strict separation between the REST API and the AI agent layer**.

The Django monolith handles everything a production web service needs — auth, data models, quotas, routing. It is stable and independently deployable.

The agent logic lives in a completely separate Python package (`backend/agent/`). It can be run, tested, and iterated on locally with zero Django dependency. This decoupling enables fast experimentation without touching the production service.

**Agent design principles:**

- **Model Context Protocol (MCP)** — the agent communicates with diagram tools through a standardized, transport-agnostic protocol. Tools are defined as MCP endpoints; the agent discovers and calls them dynamically.
- **Structured prompt optimization (DSPy)** — routing and diagram-type selection are not hand-crafted prompt strings. They are compiled programs, optimized against real examples using DSPy. This makes the decision logic testable and improvable as a function.
- **Clean interfaces** — the REST layer calls the agent through a single well-defined boundary. The agent calls diagram tools through MCP. Neither layer knows about the internals of the other.

<!-- TODO: add internal architecture diagram -->

**Agent stack:**

- **[fast-agent-mcp](https://github.com/evalstate/fast-agent)** — multi-step agentic workflow orchestration over MCP
- **[DSPy](https://dspy.ai/)** — structured prompt optimization; routing logic is compiled, not hardcoded
- **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server definition with minimal boilerplate

The **MCP tool server** (`backend/mcp_diagrams/`) exposes diagram rendering tools over HTTP. The agent selects the appropriate tool, constructs the arguments, invokes it, and returns the GCS URI of the result.

---

## Technology Summary

| Layer | Technology |
|---|---|
| Frontend | [Astro](https://astro.build/) (SSG) + [Vue.js](https://vuejs.org/) + [Tailwind CSS](https://tailwindcss.com/) |
| REST API | [Django](https://www.djangoproject.com/) + [Django REST Framework](https://www.django-rest-framework.org/) |
| Agent Orchestration | [fast-agent-mcp](https://github.com/evalstate/fast-agent) |
| Prompt Optimization | [DSPy](https://dspy.ai/) |
| Infrastructure | [Terraform](https://www.terraform.io/) on [Google Cloud Platform](https://cloud.google.com/) |
| CI/CD | [GitHub Actions](https://github.com/features/actions) |
| Code Quality | pre-commit · ruff · actionlint · gitleaks · talisman · Trivy *(planned)* |
| Observability | [OpenTelemetry](https://opentelemetry.io/) |

---

## Repository Structure

```
diagramik/
├── frontend/          # Astro SSG application
├── backend/
│   ├── django_monolith/   # REST API, auth, data models
│   ├── agent/             # AI agent (DSPy + fast-agent) — independently runnable
│   └── mcp_diagrams/      # MCP tool server for diagram rendering
└── infrastructure/    # Terraform — all GCP resources defined as code
```
