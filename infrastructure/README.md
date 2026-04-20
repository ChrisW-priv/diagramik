# Diagramik Infrastructure — Structure Map

This document is the definitive reference for the Terraform configuration. Read it before making changes.

## Tech Stack

- **Terraform** — infrastructure as code
- **GCP Provider** — all resources are on Google Cloud Platform
- **GCP Project**: `playground-449613`, region `europe-west4`

## Module Inventory

| Module            | Path                       | Purpose                                                                                                                                                |
| ----------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `django-monolith` | `modules/django-monolith/` | Cloud Run service for the Django API, Cloud SQL (PostgreSQL), GCS diagrams bucket, service account, Workload Identity Federation for CI                |
| `mcp-service`     | `modules/mcp-service/`     | Cloud Run service for the MCP diagram server (internal-only, VPC ingress)                                                                              |
| `frontend-bucket` | `modules/frontend-bucket/` | GCS bucket serving the Astro SSG static site                                                                                                           |
| `global-lb`       | `modules/global-lb/`       | Global HTTPS load balancer with CDN and path-based routing: `/api/*` → Django Cloud Run, `/share/*` → share Cloud Function, `/*` → frontend GCS bucket |
| `vpc`             | `modules/vpc/`             | Private VPC enabling Cloud SQL private IP and Cloud Run-to-Cloud SQL private connectivity                                                              |
| `secret`          | `modules/secret/`          | Secret Manager secret resources (thin wrapper used by other modules)                                                                                   |

## Top-Level Resources (`main.tf`)

Beyond the modules above, `main.tf` manages:

- Secrets: `AI_SECRET_KEY`, `DIAGRAMIK_GCS_SA_KEY`, `EMAIL_LABS_API_APP_KEY/SECRET_KEY`, `GOOGLE_OAUTH_CLIENT_ID/SECRET`
- GCS SA key for signed URL generation, with IAM binding to the diagrams bucket
- MCP service wired to the monolith's service account as the only authorized invoker

## Environments

- `environments/deployed.tfvars` — production variable values (image tags, domain, project ID)
- Pass with `TF_VAR_FILE=environments/deployed.tfvars` or via the CI workflow

## Deployment Model

Terraform is applied exclusively by the `release.yml` GitHub Actions workflow, triggered when a GitHub release is published. The workflow sets `TF_VAR_docker_image_tag` to the release git tag.

Manual `t apply` is appropriate only for initial infrastructure setup or emergency interventions. Always run `t plan` first.
