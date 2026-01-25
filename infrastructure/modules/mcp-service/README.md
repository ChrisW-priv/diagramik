# MCP Service Terraform Module

## Overview

This Terraform module provisions a complete MCP (Model Context Protocol) service on Google Cloud Platform using Cloud Run. It creates a dedicated service account with appropriate IAM permissions, grants access to a GCS bucket for diagram storage, and deploys a containerized MCP service with configurable resources and environment variables.

## Architecture

The module creates the following GCP resources:

1. **Service Account** (`google_service_account.mcp_sa`)

   - Dedicated identity for the MCP service
   - Named as `{application_name}-mcp-sa`

1. **IAM Bindings**

   - Grants `roles/storage.objectUser` on the diagrams bucket
   - Grants `roles/secretmanager.secretAccessor` for specified secrets

1. **Cloud Run Service** (via `cloudrun-service` module)

   - Containerized MCP service deployment
   - Configurable CPU, memory, and ingress settings
   - Automatic scaling and internal networking

### Resource Dependency Graph

```
google_service_account.mcp_sa
    |
    +---> google_storage_bucket_iam_member.mcp_bucket_access
    |
    +---> google_secret_manager_secret_iam_member.extra_secret_access (for_each)
    |
    +---> module.mcp-service (cloudrun-service)
           |
           +---> google_cloud_run_v2_service
```

## Requirements

- **Terraform**: >= 0.13
- **Provider**: `google` or `google-beta`
- **Dependencies**: The `cloudrun-service` module must exist at `../cloudrun-service`
- **Permissions**: The executing identity must have permissions to:
  - Create service accounts
  - Manage IAM bindings on GCS buckets and Secret Manager secrets
  - Deploy Cloud Run services

## Required Inputs

| Variable               | Type     | Description                                                                            |
| ---------------------- | -------- | -------------------------------------------------------------------------------------- |
| `google_project_id`    | `string` | The GCP project ID where resources will be created                                     |
| `location`             | `string` | The GCP region for the Cloud Run service (e.g., `us-central1`)                         |
| `application_name`     | `string` | Base name for the application (will be suffixed with `-mcp` for the service)           |
| `image_url`            | `string` | Full Docker image URL for the MCP service container (e.g., `gcr.io/project/image:tag`) |
| `diagrams_bucket_name` | `string` | Name of the GCS bucket where diagrams are stored                                       |

## Optional Inputs

### Resource Configuration

| Variable                | Type     | Default                           | Description                                                                                                                             |
| ----------------------- | -------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `memory_limit`          | `string` | `"512Mi"`                         | Memory limit for the Cloud Run container                                                                                                |
| `cpu_limit`             | `string` | `"1"`                             | CPU limit for the Cloud Run container                                                                                                   |
| `ingress`               | `string` | `"INGRESS_TRAFFIC_INTERNAL_ONLY"` | Ingress traffic sources. Valid values: `INGRESS_TRAFFIC_ALL`, `INGRESS_TRAFFIC_INTERNAL_ONLY`, `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` |
| `allow_unauthenticated` | `bool`   | `true`                            | Whether to allow unauthenticated access to the service                                                                                  |

### Environment and Configuration Extension

| Variable                | Type          | Default | Description                                                                                                            |
| ----------------------- | ------------- | ------- | ---------------------------------------------------------------------------------------------------------------------- |
| `extra_env_vars`        | `map(string)` | `{}`    | Additional environment variables merged with base config (`GCP_PROJECT_ID`, `BUCKET_NAME`)                             |
| `extra_secret_env_vars` | `map(object)` | `{}`    | Additional secret-backed environment variables. Object schema: `{secret_id: string, secret_version: optional(string)}` |
| `extra_volumes`         | `map(object)` | `{}`    | Additional volume configurations (GCS buckets, Cloud SQL instances, secrets, or emptyDir). See volume schema below     |
| `extra_volume_mounts`   | `map(string)` | `{}`    | Additional volume mounts mapping volume names to container paths                                                       |
| `extra_secret_access`   | `set(string)` | `[]`    | Set of Secret Manager secret IDs that the service account needs `secretAccessor` permission for                        |

### Volume Schema

The `extra_volumes` variable accepts a map of volume configurations with the following object schema:

```hcl
{
  # GCS-backed volume
  gcs_bucket   = optional(string)     # GCS bucket name to mount
  gcs_readonly = optional(bool, false) # Mount as read-only

  # Cloud SQL volume
  cloudsql_instances = optional(list(string)) # List of Cloud SQL instance connection names

  # Secret volume
  secret_name = optional(string) # Secret Manager secret name
  secret_items = optional(list(object({
    version = string          # Secret version
    path    = string          # Path within the volume
    mode    = optional(number, 0444) # File permissions
  })))

  # EmptyDir volume (ephemeral storage)
  emptydir_medium     = optional(string) # "Memory" for tmpfs
  emptydir_size_limit = optional(string) # Size limit (e.g., "1Gi")
}
```

## Outputs

| Output                   | Type     | Description                                                                      |
| ------------------------ | -------- | -------------------------------------------------------------------------------- |
| `service_id`             | `string` | The fully qualified ID of the Cloud Run service                                  |
| `service_name`           | `string` | The name of the Cloud Run service                                                |
| `service_uri`            | `string` | The HTTPS URI of the deployed Cloud Run service                                  |
| `location`               | `string` | The GCP region where the service is deployed                                     |
| `service_account_email`  | `string` | The email address of the created service account                                 |
| `service_account_member` | `string` | The IAM member string for the service account (format: `serviceAccount:{email}`) |

## Usage Examples

### Basic Usage

```hcl
module "mcp_service" {
  source = "./modules/mcp-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "text-diagrams"
  image_url             = "gcr.io/my-gcp-project/mcp-service:latest"
  diagrams_bucket_name  = "my-diagrams-bucket"
}
```

### Advanced Usage with Secrets and Custom Resources

```hcl
module "mcp_service" {
  source = "./modules/mcp-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "text-diagrams"
  image_url             = "gcr.io/my-gcp-project/mcp-service:v1.2.3"
  diagrams_bucket_name  = "prod-diagrams-bucket"

  # Resource limits
  memory_limit = "1Gi"
  cpu_limit    = "2"

  # Network configuration
  ingress               = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  allow_unauthenticated = false

  # Additional environment variables
  extra_env_vars = {
    "LOG_LEVEL"        = "info"
    "FEATURE_FLAG_XYZ" = "enabled"
  }

  # Secret environment variables
  extra_secret_env_vars = {
    "API_KEY" = {
      secret_id      = "mcp-api-key"
      secret_version = "latest"
    }
    "DATABASE_PASSWORD" = {
      secret_id = "db-password"
    }
  }

  # Grant access to externally-managed secrets
  extra_secret_access = [
    "mcp-api-key",
    "db-password",
    "shared-encryption-key"
  ]

  # Mount a secret as a file
  extra_volumes = {
    "credentials" = {
      secret_name = "service-credentials"
      secret_items = [
        {
          version = "1"
          path    = "key.json"
          mode    = 0400
        }
      ]
    }
  }

  extra_volume_mounts = {
    "credentials" = "/etc/secrets"
  }
}

# Access outputs
output "mcp_url" {
  value = module.mcp_service.service_uri
}

output "mcp_sa_email" {
  value = module.mcp_service.service_account_email
}
```

### Usage with Cloud SQL

```hcl
module "mcp_service" {
  source = "./modules/mcp-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "text-diagrams"
  image_url             = "gcr.io/my-gcp-project/mcp-service:latest"
  diagrams_bucket_name  = "my-diagrams-bucket"

  # Mount Cloud SQL Unix socket
  extra_volumes = {
    "cloudsql" = {
      cloudsql_instances = [
        "my-gcp-project:us-central1:my-db-instance"
      ]
    }
  }

  extra_volume_mounts = {
    "cloudsql" = "/cloudsql"
  }

  extra_env_vars = {
    "DB_SOCKET_PATH" = "/cloudsql/my-gcp-project:us-central1:my-db-instance"
  }
}
```

## Important Notes

### Base Environment Variables

The module automatically configures the following base environment variables:

- `GCP_PROJECT_ID`: Set to the value of `var.google_project_id`
- `BUCKET_NAME`: Set to the value of `var.diagrams_bucket_name`

These can be overridden using `extra_env_vars` if needed (extra takes precedence).

### IAM Permissions

The created service account receives:

1. **Automatic permissions**:

   - `roles/storage.objectUser` on the diagrams bucket (allows read/write/delete objects)

1. **Optional permissions** (via `extra_secret_access`):

   - `roles/secretmanager.secretAccessor` on specified secrets

1. **Implicit permissions** (from Cloud Run):

   - Service account must have permissions to pull the container image

Ensure the diagrams bucket exists before applying this module, or include it in the same Terraform configuration with appropriate dependencies.

### Security Considerations

- **Default ingress** is `INGRESS_TRAFFIC_INTERNAL_ONLY`, restricting access to within the VPC or via Cloud Run-supported mechanisms
- **Default authentication** allows unauthenticated access (`allow_unauthenticated = true`). For production deployments, consider setting this to `false` and implementing proper authentication
- **Secrets**: Use `extra_secret_env_vars` for sensitive data rather than `extra_env_vars`
- **Service account**: The created SA has specific, scoped permissions. Avoid granting additional broad permissions

### State Impact Considerations

- **Service account changes**: Modifying `application_name` will recreate the service account, potentially breaking existing IAM bindings
- **Bucket IAM changes**: Changing `diagrams_bucket_name` updates IAM bindings without downtime
- **Image updates**: Changing `image_url` triggers a new Cloud Run revision deployment with zero-downtime rollout
- **Resource limit changes**: Modifying `memory_limit` or `cpu_limit` creates a new revision

### Dependencies

This module depends on:

1. **Module dependency**: `cloudrun-service` module at `../cloudrun-service`
1. **Resource dependency**: The diagrams GCS bucket must exist
1. **Explicit dependency**: IAM bindings must complete before Cloud Run service deployment (handled via `depends_on`)

### Limitations

- The module creates a single Cloud Run service per invocation
- IAM permissions are managed per-secret; bulk secret access requires individual entries in `extra_secret_access`
- The service account naming is fixed as `{application_name}-mcp-sa`

## Troubleshooting

### Permission Denied on Secret Access

If the service fails to access secrets:

1. Verify the secret ID is included in `extra_secret_access`
1. Ensure the secret exists in the same project
1. Check that the IAM binding has propagated (can take up to 80 seconds)

### Container Fails to Start

1. Verify the `image_url` is correct and accessible
1. Check that the service account has permission to pull from the container registry
1. Review Cloud Run logs for startup errors
1. Ensure resource limits (`memory_limit`, `cpu_limit`) are sufficient

### Bucket Access Issues

1. Confirm the bucket name in `diagrams_bucket_name` is correct
1. Verify the bucket exists in the same project
1. Check IAM bindings on the bucket manually if needed

## Migration and Upgrade Paths

When upgrading this module or changing significant parameters:

1. **Test in non-production first**: Always validate changes in a development environment
1. **Review state plan carefully**: Use `terraform plan` to understand what will change
1. **Service account recreation**: If renaming the application, plan for IAM binding recreation
1. **Backup considerations**: Ensure diagrams bucket has versioning enabled for data protection
