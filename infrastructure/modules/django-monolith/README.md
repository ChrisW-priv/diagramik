# Django Monolith Terraform Module

This Terraform module provisions a complete Django application infrastructure on Google Cloud Platform (GCP). It creates a production-ready Django monolith deployment with Cloud Run, PostgreSQL database, storage buckets, artifact registry, and all necessary supporting resources.

## Overview

This module sets up a comprehensive Django application environment including:

- **Cloud Run Service**: Django application deployed as a containerized service with load balancer ingress
- **Cloud SQL (PostgreSQL)**: Managed PostgreSQL database with automated backups
- **Storage Buckets**: Three GCS buckets for diagrams, public static files, and private media
- **Artifact Registry**: Docker image repository for application containers
- **Service Account**: Dedicated service account with minimal required permissions
- **Secret Management**: Managed secrets for database credentials and Django secret key
- **Setup Job**: Cloud Run Job for running Django migrations and initial setup
- **Workload Identity**: Optional GitHub Actions integration for CI/CD workflows

## Architecture

The module creates the following resource topology:

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Monolith Module                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   Cloud Run      │────────>│   Service        │          │
│  │   Django Service │         │   Account        │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                            │                     │
│           │                            │                     │
│           ▼                            ▼                     │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   Cloud SQL      │         │   Secret Manager │          │
│  │   PostgreSQL     │         │   - DB Password  │          │
│  └──────────────────┘         │   - Secret Key   │          │
│                                │   - Admin Pass   │          │
│                                └──────────────────┘          │
│                                                               │
│  ┌──────────────────────────────────────────────┐            │
│  │            Storage Buckets                   │            │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ │            │
│  │  │ Diagrams   │ │   Public   │ │ Private  │ │            │
│  │  │   Bucket   │ │   Bucket   │ │  Bucket  │ │            │
│  │  └────────────┘ └────────────┘ └──────────┘ │            │
│  └──────────────────────────────────────────────┘            │
│                                                               │
│  ┌──────────────────┐         ┌──────────────────┐          │
│  │   Artifact       │         │   Cloud Run      │          │
│  │   Registry       │<────────│   Setup Job      │          │
│  └──────────────────┘         └──────────────────┘          │
│           │                                                   │
│           └──> Docker Images: application-monolith,          │
│                diagramming-mcp                               │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Terraform**: >= 1.0
- **Provider**: Google Cloud Platform
- **GCP APIs**: The following APIs must be enabled in your project:
  - Cloud Run API (`run.googleapis.com`)
  - Cloud SQL Admin API (`sqladmin.googleapis.com`)
  - Secret Manager API (`secretmanager.googleapis.com`)
  - Artifact Registry API (`artifactregistry.googleapis.com`)
  - Cloud Storage API (`storage.googleapis.com`)

## Dependencies

This module depends on the following child modules (must exist in the specified paths):

- `../artifact-registry` - Creates and manages GCP Artifact Registry repositories
- `../storage-bucket` - Creates and manages GCS buckets with permissions
- `../secret` - Manages Secret Manager secrets and IAM bindings
- `../cloudsql` - Provisions Cloud SQL PostgreSQL instances
- `../cloudrun-job` - Creates Cloud Run Jobs
- `../cloudrun-service` - Creates Cloud Run Services

## Variables

### Required Variables

| Name                | Type     | Description                                                           |
| ------------------- | -------- | --------------------------------------------------------------------- |
| `google_project_id` | `string` | The GCP project ID where resources will be created                    |
| `location`          | `string` | The GCP region/location for resource deployment (e.g., `us-central1`) |
| `application_name`  | `string` | The application name used as a prefix for all resources               |

### Optional Variables

| Name                           | Type          | Default    | Description                                                                                                                 |
| ------------------------------ | ------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| `docker_image_tag`             | `string`      | `"latest"` | Docker image tag (commit SHA or version) to deploy                                                                          |
| `github_repository`            | `string`      | `""`       | GitHub repository in `owner/repo` format for Workload Identity Federation (CI/CD integration)                               |
| `workload_identity_pool_id`    | `string`      | `""`       | The full ID of the Workload Identity Pool (e.g., `projects/123/locations/global/workloadIdentityPools/github`)              |
| `extra_django_env_vars`        | `map(string)` | `{}`       | Additional environment variables to add to the Django service. These merge with base configuration and take precedence      |
| `extra_django_secret_env_vars` | `map(object)` | `{}`       | Additional secret-backed environment variables. Object structure: `{secret_id = string, secret_version = optional(string)}` |
| `extra_django_volumes`         | `map(object)` | `{}`       | Additional volumes to mount (GCS buckets, Cloud SQL instances, secrets, or emptyDir). See volume object structure below     |
| `extra_django_volume_mounts`   | `map(string)` | `{}`       | Volume mount paths mapped to volume names. Format: `{volume_name = "/mount/path"}`                                          |
| `extra_secret_access`          | `set(string)` | `[]`       | Set of externally-managed Secret Manager secret IDs that the service account should access                                  |

#### Volume Object Structure

For `extra_django_volumes`, each volume supports the following optional fields:

```hcl
{
  gcs_bucket         = optional(string)           # GCS bucket name for GCS volume
  gcs_readonly       = optional(bool, false)      # Mount GCS bucket as read-only
  cloudsql_instances = optional(list(string))     # Cloud SQL connection names
  secret_name        = optional(string)           # Secret Manager secret name
  secret_items = optional(list(object({           # Secret items to mount
    version = string                              # Secret version
    path    = string                              # File path within mount
    mode    = optional(number, 0444)              # File permissions
  })))
  emptydir_medium     = optional(string)          # EmptyDir medium (Memory or Disk)
  emptydir_size_limit = optional(string)          # EmptyDir size limit
}
```

## Outputs

| Name                      | Type     | Description                                                                |
| ------------------------- | -------- | -------------------------------------------------------------------------- |
| `service_account_email`   | `string` | Email address of the created service account                               |
| `service_account_member`  | `string` | IAM member string for the service account (format: `serviceAccount:email`) |
| `django_service_name`     | `string` | Name of the Cloud Run service running Django                               |
| `django_service_uri`      | `string` | Full HTTPS URI of the Django Cloud Run service                             |
| `django_service_location` | `string` | GCP region where the Django service is deployed                            |
| `artifact_registry_url`   | `string` | Base URL of the Artifact Registry repository                               |
| `diagrams_bucket_name`    | `string` | Name of the GCS bucket storing diagram files                               |
| `mcp_image_url`           | `string` | Full Docker image URL for the MCP (diagramming) container                  |

## Usage Example

### Basic Usage

```hcl
module "django_app" {
  source = "./modules/django-monolith"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  application_name  = "diagramik"
  docker_image_tag  = "v1.2.3"
}
```

### Production Usage with GitHub Actions CI/CD

```hcl
module "django_app" {
  source = "./modules/django-monolith"

  google_project_id         = "my-production-project"
  location                  = "us-central1"
  application_name          = "diagramik"
  docker_image_tag          = var.commit_sha
  github_repository         = "myorg/myrepo"
  workload_identity_pool_id = "projects/123456789/locations/global/workloadIdentityPools/github"
}

output "service_url" {
  value = module.django_app.django_service_uri
}
```

### Advanced Usage with Custom Configuration

This example demonstrates mounting external secrets as files and passing custom environment variables:

```hcl
# First, create external secrets
module "api_key_secret" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "EXTERNAL_API_KEY"
  secret_data       = var.api_key
}

module "service_account_key" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "GCS_SERVICE_ACCOUNT_KEY"
  secret_data       = var.gcs_sa_key_json
}

# Deploy Django with custom configuration
module "django_app" {
  source = "./modules/django-monolith"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  application_name  = "diagramik"
  docker_image_tag  = "v2.0.0"

  # Mount secrets as files
  extra_django_volumes = {
    "gcs-credentials" = {
      secret_name = module.service_account_key.secret_id
      secret_items = [
        {
          version = "latest"
          path    = "key.json"
          mode    = 0400  # Read-only for owner
        }
      ]
    }
  }

  extra_django_volume_mounts = {
    "gcs-credentials" = "/secrets/gcs"
  }

  # Additional environment variables
  extra_django_env_vars = {
    "GCS_CREDENTIALS_PATH" = "/secrets/gcs/key.json"
    "FEATURE_FLAG_XYZ"     = "enabled"
    "LOG_LEVEL"            = "DEBUG"
  }

  # Additional secret environment variables
  extra_django_secret_env_vars = {
    "EXTERNAL_API_KEY" = {
      secret_id      = module.api_key_secret.secret_id
      secret_version = "latest"
    }
  }

  # Grant access to external secrets
  extra_secret_access = [
    module.api_key_secret.secret_id,
    module.service_account_key.secret_id
  ]

  # Ensure secrets exist before creating IAM bindings
  depends_on = [
    module.api_key_secret,
    module.service_account_key
  ]
}
```

## Resource Naming Convention

All resources created by this module follow a consistent naming pattern:

- **Service Account**: `{application_name}-sa`
- **Artifact Registry**: `{application_name}`
- **Storage Buckets**:
  - `{application_name}-diagrams`
  - `{application_name}-public`
  - `{application_name}-private`
- **Cloud SQL Instance**: `django-monolith-postgres`
- **Cloud Run Service**: `{application_name}`
- **Cloud Run Job**: `{application_name}-setup-job`

## Base Configuration

The module automatically configures the Django service with these base settings:

### Environment Variables

```hcl
LOGGING_LEVEL          = "INFO"
GCP_PROJECT_ID         = var.google_project_id
DIAGRAMS_BUCKET_NAME   = "{application_name}-diagrams"
STATIC_BUCKET_NAME     = "{application_name}-public"
MEDIA_BUCKET_NAME      = "{application_name}-private"
DB_CONN_NAME           = "project:region:instance"
POSTGRES_DATABASE_NAME = "postgres"
POSTGRES_USER          = "postgres"
DEPLOYMENT_ENVIRONMENT = "PRODUCTION_SERVICE"
```

### Secret Environment Variables

```hcl
POSTGRES_PASSWORD   = secret("db-password")
DEFAULT_SECRET_KEY  = secret("django-secret-key")
```

### Volumes

- **Cloud SQL Proxy**: Mounted at `/cloudsql` for database connectivity

All base configurations can be extended using the `extra_*` variables, which take precedence in case of conflicts.

## Important Notes

### State Impact Considerations

- **Destructive Changes**: Modifying `application_name` will cause all resources to be recreated (database data loss)
- **Database Recreation**: Changing Cloud SQL configuration may require database recreation - backup data first
- **Secret Rotation**: Manually rotating secrets in Secret Manager does not trigger service redeployment
- **Image Updates**: Changing `docker_image_tag` triggers Cloud Run service redeployment with zero downtime

### Security Best Practices

1. **Secrets Management**:

   - Never commit secret values to version control
   - Use Secret Manager for all sensitive data
   - Rotate secrets regularly (especially `DJANGO_MONOLITH_SECRET_KEY`)

1. **Service Account Permissions**:

   - The module creates a dedicated service account with minimal required permissions
   - Avoid granting additional broad IAM roles to this service account

1. **Network Security**:

   - Cloud Run service uses `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` by default
   - Database is accessible only via Cloud SQL Proxy (no public IP)
   - Public bucket allows `allUsers` to read objects (intended for static assets)

1. **Workload Identity**:

   - When using GitHub Actions, only specify repositories you control
   - The repository format must be exact: `owner/repo-name`

### Database Initialization

After the module is applied for the first time:

1. Manually set the `DJANGO_MONOLITH_ADMIN_PASSWORD` secret value:

   ```bash
   echo -n "your-secure-password" | gcloud secrets versions add DJANGO_MONOLITH_ADMIN_PASSWORD --data-file=-
   ```

1. Execute the setup job to run migrations and create the superuser:

   ```bash
   gcloud run jobs execute {application_name}-setup-job --region={location}
   ```

1. Verify the Django service is accessible via the output `django_service_uri`

### Dependency Chain

The module implements a careful dependency chain to ensure resources are created in the correct order:

```
Secrets Created → Service Account → IAM Bindings → Cloud Run Service
Database Created → Setup Job
```

The `extra_secrets_ready` resource anchor ensures external secrets exist before IAM bindings are created, preventing race conditions.

### Cost Optimization

- Cloud Run scales to zero when not in use (pay only for requests)
- Cloud SQL instance runs continuously (consider shutting down dev environments when unused)
- Storage buckets charge for storage and egress (monitor public bucket traffic)
- Artifact Registry charges for storage (clean up old images regularly)

## Troubleshooting

### Service won't start

1. Check Cloud Run logs: `gcloud run services logs read {application_name} --region={location}`
1. Verify all secrets have values set in Secret Manager
1. Ensure database migrations completed successfully (check setup job logs)

### Database connection failures

1. Verify Cloud SQL Proxy volume is mounted at `/cloudsql`
1. Check service account has `roles/cloudsql.client` role
1. Confirm `DB_CONN_NAME` format: `project:region:instance`

### Permission denied errors

1. Review service account IAM bindings
1. Check `extra_secret_access` includes all external secrets
1. Verify Secret Manager secret versions exist

## Migration Guide

If migrating from manual infrastructure to this module:

1. **Import Existing Resources** (if applicable):

   ```bash
   terraform import module.django_app.google_service_account.sa projects/{project}/serviceAccounts/{email}
   terraform import module.django_app.module.postgres_db.google_sql_database_instance.main {instance-name}
   ```

1. **State Migration**: If renaming resources, use `moved` blocks:

   ```hcl
   moved {
     from = module.old_django
     to   = module.django_app
   }
   ```

1. **Data Migration**: For Cloud SQL, export data before recreating:

   ```bash
   gcloud sql export sql {instance} gs://{bucket}/backup.sql --database={db}
   ```

## License

This module is part of the text-diagrams project infrastructure.
