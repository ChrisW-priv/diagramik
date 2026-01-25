# Cloud Run Service Terraform Module

This Terraform module creates and configures a Google Cloud Run v2 service with comprehensive support for volumes, environment variables, secrets, autoscaling, and IAM policies.

## Overview

This module provisions:

- **Google Cloud Run v2 Service**: Fully managed serverless container platform
- **API Enablement**: Automatically enables the Cloud Run API (`run.googleapis.com`)
- **IAM Configuration**: Optional public access via `allUsers` invoker role
- **Volume Support**: GCS buckets, Cloud SQL instances, Secret Manager secrets, and EmptyDir volumes
- **Environment Configuration**: Standard environment variables and Secret Manager-backed secret environment variables
- **Autoscaling**: Configurable min/max instance counts
- **Resource Limits**: CPU and memory constraints

## Module Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Cloud Run v2 Service                                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Container: app                                   │  │
│  │  - Image: var.image_url                           │  │
│  │  - Port: var.port_number (default: 8080)          │  │
│  │  - Resources: CPU & Memory limits                 │  │
│  │  - Env Vars: Plain text + Secret Manager refs    │  │
│  │  - Volume Mounts: Multiple volume types           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  Volumes (dynamic):                                      │
│  - GCS buckets (read-only or read-write)                │
│  - Cloud SQL instances                                  │
│  - Secret Manager secrets                               │
│  - EmptyDir (ephemeral storage)                         │
│                                                          │
│  Scaling:                                                │
│  - Min instances: var.min_instance_count (default: 0)   │
│  - Max instances: var.max_instance_count (default: 1)   │
│                                                          │
│  Service Account: var.service_account_email             │
└─────────────────────────────────────────────────────────┘
              │
              │ (optional)
              ▼
    ┌──────────────────────┐
    │  IAM Binding         │
    │  roles/run.invoker   │
    │  member: allUsers    │
    └──────────────────────┘
    (if allow_unauthenticated = true)
```

## Requirements

- **Terraform**: >= 0.13 (for optional object attributes)
- **Google Provider**: Configured with appropriate credentials
- **GCP APIs**: The module automatically enables `run.googleapis.com`
- **Service Account**: Pre-existing service account with appropriate permissions

## Required Inputs

| Name                    | Type     | Description                                                    |
| ----------------------- | -------- | -------------------------------------------------------------- |
| `google_project_id`     | `string` | The GCP project ID where resources will be created             |
| `location`              | `string` | The GCP region for the Cloud Run service (e.g., `us-central1`) |
| `application_name`      | `string` | The name of the Cloud Run service                              |
| `service_account_email` | `string` | Email of the service account the Cloud Run service will run as |
| `image_url`             | `string` | Full Docker image URL (e.g., `gcr.io/project/image:tag`)       |

## Optional Inputs

| Name                    | Type          | Default                           | Description                                                                                                                  |
| ----------------------- | ------------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `port_name`             | `string`      | `"h2c"`                           | Protocol for the container port (h2c for HTTP/2, http1 for HTTP/1)                                                           |
| `port_number`           | `number`      | `8080`                            | Container port number to expose                                                                                              |
| `min_instance_count`    | `number`      | `0`                               | Minimum number of instances (0 allows scale-to-zero)                                                                         |
| `max_instance_count`    | `number`      | `1`                               | Maximum number of instances for autoscaling                                                                                  |
| `cpu_limit`             | `string`      | `"1"`                             | CPU allocation (e.g., "1", "2", "4")                                                                                         |
| `memory_limit`          | `string`      | `"1Gi"`                           | Memory limit (e.g., "512Mi", "1Gi", "2Gi")                                                                                   |
| `ingress`               | `string`      | `"INGRESS_TRAFFIC_INTERNAL_ONLY"` | Ingress traffic control: `INGRESS_TRAFFIC_ALL`, `INGRESS_TRAFFIC_INTERNAL_ONLY`, or `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` |
| `allow_unauthenticated` | `bool`        | `false`                           | Allow public access without authentication (grants `allUsers` the `roles/run.invoker` role)                                  |
| `env_vars`              | `map(string)` | `{}`                              | Map of plain-text environment variables                                                                                      |
| `secret_env_vars`       | `map(object)` | `{}`                              | Map of Secret Manager-backed environment variables (see below)                                                               |
| `volumes`               | `map(object)` | `{}`                              | Map of volume configurations (see below)                                                                                     |
| `volume_mounts`         | `map(string)` | `{}`                              | Map of volume mount paths (key = volume name, value = mount path)                                                            |

### Secret Environment Variables

The `secret_env_vars` variable accepts a map of objects with the following structure:

```hcl
secret_env_vars = {
  "ENV_VAR_NAME" = {
    secret_id      = "projects/PROJECT_ID/secrets/SECRET_NAME"  # Required
    secret_version = "latest"  # Optional, defaults to "latest"
  }
}
```

### Volume Configuration

The `volumes` variable supports four volume types. Each volume is identified by a unique key in the map, and the type is inferred from which fields are set:

#### GCS Volume

```hcl
volumes = {
  "gcs-data" = {
    gcs_bucket   = "my-bucket-name"  # Required for GCS
    gcs_readonly = false              # Optional, defaults to false
  }
}
```

#### Cloud SQL Volume

```hcl
volumes = {
  "cloudsql" = {
    cloudsql_instances = [  # Required for Cloud SQL
      "project:region:instance-name"
    ]
  }
}
```

#### Secret Manager Volume

```hcl
volumes = {
  "secret-vol" = {
    secret_name = "projects/PROJECT_ID/secrets/SECRET_NAME"  # Required
    secret_items = [  # Optional
      {
        version = "latest"
        path    = "secret-file.json"
        mode    = 0444  # Optional, defaults to 0444
      }
    ]
  }
}
```

#### EmptyDir Volume

```hcl
volumes = {
  "tmp" = {
    emptydir_medium     = "MEMORY"  # Optional: "MEMORY" or null (disk)
    emptydir_size_limit = "1Gi"     # Optional: size limit
  }
}
```

## Outputs

| Name           | Type     | Description                                     |
| -------------- | -------- | ----------------------------------------------- |
| `service_id`   | `string` | The fully qualified ID of the Cloud Run service |
| `service_name` | `string` | The name of the Cloud Run service               |
| `service_uri`  | `string` | The HTTPS URI of the Cloud Run service          |
| `location`     | `string` | The location (region) of the Cloud Run service  |

## Usage Examples

### Basic Example

Minimal configuration for a simple Cloud Run service:

```hcl
module "api_service" {
  source = "./modules/cloudrun-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "my-api"
  service_account_email = "my-service@my-gcp-project.iam.gserviceaccount.com"
  image_url             = "gcr.io/my-gcp-project/my-api:latest"
}
```

### Public Service with Custom Resources

Service accessible to the internet with increased resources:

```hcl
module "public_api" {
  source = "./modules/cloudrun-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "public-api"
  service_account_email = "api-sa@my-gcp-project.iam.gserviceaccount.com"
  image_url             = "gcr.io/my-gcp-project/api:v1.2.3"

  # Public access
  ingress               = "INGRESS_TRAFFIC_ALL"
  allow_unauthenticated = true

  # Scaling
  min_instance_count = 1  # Always-on
  max_instance_count = 10

  # Resources
  cpu_limit    = "2"
  memory_limit = "2Gi"

  # Environment variables
  env_vars = {
    "LOG_LEVEL"    = "INFO"
    "API_VERSION"  = "v1"
  }
}
```

### Advanced Example with Database and Secrets

Full-featured Django application with Cloud SQL, Secret Manager, and GCS:

```hcl
module "django_app" {
  source = "./modules/cloudrun-service"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  application_name      = "django-backend"
  service_account_email = google_service_account.app_sa.email
  image_url             = "gcr.io/my-gcp-project/django-app:latest"

  # Load balancer access only
  ingress               = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  allow_unauthenticated = true

  # Scaling
  min_instance_count = 1
  max_instance_count = 5

  # Resources
  cpu_limit    = "2"
  memory_limit = "4Gi"

  # Volumes
  volumes = {
    # Cloud SQL connection
    "cloudsql" = {
      cloudsql_instances = [
        "my-gcp-project:us-central1:postgres-main"
      ]
    }
    # Secret files
    "app-secrets" = {
      secret_name = "projects/my-gcp-project/secrets/APP_SECRETS"
      secret_items = [
        {
          version = "latest"
          path    = "config.yaml"
          mode    = 0444
        }
      ]
    }
    # GCS bucket for uploads
    "uploads" = {
      gcs_bucket   = "my-app-uploads"
      gcs_readonly = false
    }
  }

  # Mount paths
  volume_mounts = {
    "cloudsql"     = "/cloudsql"
    "app-secrets"  = "/secrets"
    "uploads"      = "/mnt/uploads"
  }

  # Environment variables
  env_vars = {
    "DB_CONN_NAME"    = "my-gcp-project:us-central1:postgres-main"
    "POSTGRES_USER"   = "django_user"
    "UPLOADS_PATH"    = "/mnt/uploads"
    "CONFIG_PATH"     = "/secrets/config.yaml"
  }

  # Secret environment variables
  secret_env_vars = {
    "POSTGRES_PASSWORD" = {
      secret_id = "projects/my-gcp-project/secrets/DB_PASSWORD"
    }
    "DJANGO_SECRET_KEY" = {
      secret_id      = "projects/my-gcp-project/secrets/DJANGO_SECRET"
      secret_version = "2"  # Pin to specific version
    }
  }
}
```

### Example from This Repository

Real-world usage from `infrastructure/modules/django-monolith/main.tf`:

```hcl
module "django-monolith" {
  source                = "../cloudrun-service"
  google_project_id     = var.google_project_id
  application_name      = var.application_name
  location              = var.location
  image_url             = local.backend_monolith_image_url
  service_account_email = google_service_account.sa.email
  ingress               = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  allow_unauthenticated = true

  volumes = {
    "cloudsql" = {
      cloudsql_instances = [module.postgres_db.connection_name]
    }
    "gcs-sa-key" = {
      secret_name = module.gcs-sa-key-secret.secret_id
      secret_items = [{
        version = "latest"
        path    = "key.json"
      }]
    }
  }

  volume_mounts = {
    "cloudsql"    = "/cloudsql"
    "gcs-sa-key"  = "/secrets/gcs"
  }

  env_vars = {
    "DB_CONN_NAME"         = module.postgres_db.connection_name
    "DIAGRAMS_BUCKET_NAME" = module.diagrams-bucket.name
    "GCS_SA_KEY_PATH"      = "/secrets/gcs/key.json"
  }

  secret_env_vars = {
    "POSTGRES_PASSWORD" = {
      secret_id = module.postgres_db.db_password_secret_id
    }
    "DEFAULT_SECRET_KEY" = {
      secret_id = module.django-monolith-secret-key.secret_id
    }
  }
}
```

## Important Notes

### State Impact and Lifecycle Considerations

- **Service Recreation**: Changing `application_name`, `location`, or `google_project_id` will destroy and recreate the service
- **Deletion Protection**: Set to `false` by default. The service can be deleted via Terraform
- **API Dependencies**: The module uses `depends_on` to ensure the Cloud Run API is enabled before creating the service
- **Zero-Downtime Changes**: Most configuration changes (env vars, scaling, resources) can be applied without downtime

### Security Best Practices

1. **Service Accounts**: Use dedicated service accounts with minimal required permissions
1. **Ingress Control**: Default is `INGRESS_TRAFFIC_INTERNAL_ONLY` for security. Only use `INGRESS_TRAFFIC_ALL` when necessary
1. **Authentication**: `allow_unauthenticated` defaults to `false`. Enable public access intentionally
1. **Secrets**: Use `secret_env_vars` instead of `env_vars` for sensitive data
1. **IAM Bindings**: Grant Secret Manager access (`roles/secretmanager.secretAccessor`) to the service account for any secrets referenced
1. **Cloud SQL**: Ensure service account has `roles/cloudsql.client` role for Cloud SQL connectivity

### Volume Considerations

- **Cloud SQL**: Requires the Cloud SQL Admin API to be enabled and appropriate IAM permissions
- **Secret Manager**: The service account needs `roles/secretmanager.secretAccessor` on referenced secrets
- **GCS Buckets**: Service account needs appropriate storage permissions (typically `roles/storage.objectUser`)
- **EmptyDir**: Data is ephemeral and lost when the instance scales down
- **Volume Mounts**: Keys in `volume_mounts` must match keys in `volumes`

### Autoscaling Behavior

- **Scale-to-Zero**: `min_instance_count = 0` enables cost savings but adds cold start latency
- **Always-On**: `min_instance_count >= 1` maintains warm instances for consistent performance
- **Max Instances**: Setting `max_instance_count` too low can cause request queuing during traffic spikes

### Port Configuration

- **h2c**: HTTP/2 cleartext (default) - recommended for most use cases
- **http1**: HTTP/1 - use only if application doesn't support HTTP/2
- **Port Number**: Most containers use 8080, but customize as needed

### Resource Limits

- Valid CPU values: "1", "2", "4", "6", "8"
- Memory must be specified with units: "512Mi", "1Gi", "2Gi", etc.
- CPU and memory must maintain valid ratios per Cloud Run specifications

## Troubleshooting

### Service won't start

- Verify the Docker image exists and is accessible
- Check service account has permission to pull from the container registry
- Review Cloud Run logs for container startup errors
- Ensure port configuration matches application

### Permission Errors

- Verify service account has required IAM roles:
  - `roles/cloudsql.client` for Cloud SQL access
  - `roles/secretmanager.secretAccessor` for secrets
  - Storage roles for GCS buckets
- Check that secrets and resources exist in the correct project

### Scaling Issues

- Verify CPU and memory limits are appropriate for workload
- Check if max instances is too restrictive
- Review Cloud Run metrics for throttling or quota issues

## License

This module is part of the text-diagrams infrastructure.
