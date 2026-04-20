# Diagramik CI/CD — Structure Map

GitHub Actions is the CI/CD platform. All workflows are in `.github/workflows/`.

## Workflow Inventory

| Workflow     | File            | Trigger                                         | Purpose                              |
| ------------ | --------------- | ----------------------------------------------- | ------------------------------------ |
| Claude Code  | `claude.yml`    | Issue comments, PR reviews, issues with @claude | Claude Code AI assistant integration |
| Push to Main | `main-push.yml` | Push to `main` branch                           | Build Docker images and push to GHCR |
| Release      | `release.yml`   | GitHub release published                        | Full deploy pipeline                 |

## Pipeline Architecture

### Push to Main (`main-push.yml`)

Runs on every merge to `main`. Builds `application-monolith` and `diagramming-mcp` Docker images and pushes them to GHCR as `latest`. Used as a build cache source for the release pipeline.

### Release (`release.yml`)

Triggered when a GitHub release is published. Full end-to-end deploy:

1. Build both Docker images tagged with the git release tag
1. Push to GHCR (cache) and Google Artifact Registry (production)
1. Tag images as `latest` on GHCR
1. Run Terraform (`t init && t apply`) to update GCP infrastructure with the new image tag
1. Build and deploy `share-diagram-image` Cloud Function via Cloud Build
1. Build and deploy `render-diagram` Cloud Function via Cloud Build
1. Install frontend deps and run `t publish` to build Astro SSG and upload to GCS

### GCP Authentication

GCP auth uses **OIDC Workload Identity Federation** — no long-lived service account key is stored as a GitHub secret. The `release.yml` workflow uses `google-github-actions/auth@v2` with the WIF provider configured in Terraform (`modules/django-monolith`).

### Container Registries

- **GHCR** (`ghcr.io/chrisw-priv/...`) — used for build caching and as a secondary registry
- **GAR** (`europe-west4-docker.pkg.dev/playground-449613/diagramik/...`) — production registry; Cloud Run pulls images from here
