# Cloud Run Job Module

This Terraform module provisions a Google Cloud Run v2 Job with comprehensive support for container configuration, volumes (GCS, Cloud SQL, secrets, emptyDir), environment variables, and resource limits.

## Overview

This module creates:

- **Google Cloud Run v2 Job** - A containerized job that can be executed on-demand or scheduled
- **Google Project Services** - Enables the Cloud Run API (`run.googleapis.com`) in the specified project

The module supports flexible volume configurations including GCS buckets, Cloud SQL instances, Secret Manager secrets, and ephemeral storage. It provides granular control over container resources, retry behavior, and both plain-text and secret-sourced environment variables.

## Resources Created

| Resource Type                               | Description                                   |
| ------------------------------------------- | --------------------------------------------- |
| `google_project_service.service`            | Enables required GCP APIs (Cloud Run)         |
| `google_cloud_run_v2_job.backend_setup_job` | Cloud Run v2 Job with container configuration |

## Requirements

| Name      | Version |
| --------- | ------- |
| terraform | >= 1.0  |
| google    | >= 5.0  |

## Required Inputs

The following variables are required:

| Name                    | Type           | Description                                                                             |
| ----------------------- | -------------- | --------------------------------------------------------------------------------------- |
| `google_project_id`     | `string`       | The GCP project ID where resources will be created                                      |
| `location`              | `string`       | The GCP region where the Cloud Run Job will be deployed (e.g., `us-central1`)           |
| `name`                  | `string`       | The name of the Cloud Run Job                                                           |
| `command`               | `list(string)` | The command to run in the container (e.g., `["/app/entrypoint.sh"]`)                    |
| `args`                  | `list(string)` | The arguments to pass to the command (e.g., `["migrate", "--noinput"]`)                 |
| `service_account_email` | `string`       | The email address of the service account that the job will run as                       |
| `image_url`             | `string`       | The fully qualified Docker image URL (e.g., `us-docker.pkg.dev/project/repo/image:tag`) |

## Optional Inputs

| Name              | Type          | Default | Description                                                               |
| ----------------- | ------------- | ------- | ------------------------------------------------------------------------- |
| `memory_limit`    | `string`      | `"1Gi"` | Memory limit for the job container (e.g., `"512Mi"`, `"2Gi"`)             |
| `cpu_limit`       | `string`      | `"1"`   | CPU limit for the job container (e.g., `"0.5"`, `"2"`)                    |
| `max_retries`     | `number`      | `0`     | Maximum number of retries for failed job executions                       |
| `env_vars`        | `map(string)` | `{}`    | Map of plain-text environment variables to set in the container           |
| `secret_env_vars` | `map(object)` | `{}`    | Map of environment variables sourced from Secret Manager secrets          |
| `volumes`         | `map(object)` | `{}`    | Map of volume configurations (supports GCS, Cloud SQL, secrets, emptyDir) |
| `volume_mounts`   | `map(string)` | `{}`    | Map of volume names to mount paths in the container                       |

### Volume Configuration

The `volumes` variable accepts a map where each key is the volume name and the value is an object with the following optional fields:

**GCS Volume** (set `gcs_bucket` to enable):

- `gcs_bucket` - GCS bucket name to mount
- `gcs_readonly` - Whether to mount the bucket as read-only (default: `false`)

**Cloud SQL Volume** (set `cloudsql_instances` to enable):

- `cloudsql_instances` - List of Cloud SQL instance connection names

**Secret Volume** (set `secret_name` to enable):

- `secret_name` - Name of the Secret Manager secret
- `secret_items` - Optional list of specific secret versions to mount:
  - `version` - Secret version (e.g., `"latest"`, `"1"`)
  - `path` - Path within the volume to mount the secret
  - `mode` - File permissions (default: `0444`)

**EmptyDir Volume** (set `emptydir_medium` to enable):

- `emptydir_medium` - Storage medium (e.g., `"Memory"`)
- `emptydir_size_limit` - Size limit for the volume (e.g., `"1Gi"`)

### Secret Environment Variables

The `secret_env_vars` variable accepts a map where each key is the environment variable name and the value is an object with:

- `secret_id` - The Secret Manager secret ID
- `secret_version` - Optional secret version (defaults to `"latest"`)

## Outputs

This module does not currently export any outputs. The Cloud Run Job can be referenced using the resource name: `google_cloud_run_v2_job.backend_setup_job`

## Usage Examples

### Basic Job

```hcl
module "simple_job" {
  source = "./modules/cloudrun-job"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  name                  = "my-simple-job"
  image_url             = "gcr.io/my-project/my-image:latest"
  service_account_email = "my-sa@my-project.iam.gserviceaccount.com"
  command               = ["/bin/bash"]
  args                  = ["-c", "echo 'Hello World'"]
}
```

### Job with Cloud SQL and Secrets

```hcl
module "database_migration_job" {
  source = "./modules/cloudrun-job"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  name                  = "db-migration-job"
  image_url             = "us-docker.pkg.dev/my-project/repo/app:v1.0.0"
  service_account_email = "migration-sa@my-project.iam.gserviceaccount.com"
  command               = ["/app/entrypoint.sh"]
  args                  = ["migrate"]

  memory_limit = "2Gi"
  cpu_limit    = "2"
  max_retries  = 3

  # Mount Cloud SQL instance
  volumes = {
    "cloudsql" = {
      cloudsql_instances = ["my-project:us-central1:my-db-instance"]
    }
  }

  volume_mounts = {
    "cloudsql" = "/cloudsql"
  }

  # Plain-text environment variables
  env_vars = {
    "DB_CONN_NAME"           = "my-project:us-central1:my-db-instance"
    "POSTGRES_DATABASE_NAME" = "myapp"
    "POSTGRES_USER"          = "myapp_user"
  }

  # Secret environment variables from Secret Manager
  secret_env_vars = {
    "POSTGRES_PASSWORD" = {
      secret_id = "db-password"
    }
    "API_KEY" = {
      secret_id      = "api-key"
      secret_version = "2"
    }
  }
}
```

### Job with Secret Volume Mount

```hcl
module "job_with_secret_files" {
  source = "./modules/cloudrun-job"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  name                  = "job-with-secrets"
  image_url             = "us-docker.pkg.dev/my-project/repo/app:latest"
  service_account_email = "app-sa@my-project.iam.gserviceaccount.com"
  command               = ["/app/process.sh"]
  args                  = []

  # Mount secret as files
  volumes = {
    "gcs-credentials" = {
      secret_name = "gcs-service-account-key"
      secret_items = [
        {
          version = "latest"
          path    = "key.json"
          mode    = 0444
        }
      ]
    }
  }

  volume_mounts = {
    "gcs-credentials" = "/secrets"
  }

  env_vars = {
    "GOOGLE_APPLICATION_CREDENTIALS" = "/secrets/key.json"
  }
}
```

### Job with GCS Bucket Mount

```hcl
module "job_with_gcs" {
  source = "./modules/cloudrun-job"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  name                  = "data-processing-job"
  image_url             = "us-docker.pkg.dev/my-project/repo/processor:latest"
  service_account_email = "processor-sa@my-project.iam.gserviceaccount.com"
  command               = ["/app/process_data.sh"]
  args                  = []

  # Mount GCS bucket as read-only
  volumes = {
    "data-bucket" = {
      gcs_bucket   = "my-data-bucket"
      gcs_readonly = true
    }
  }

  volume_mounts = {
    "data-bucket" = "/data"
  }
}
```

### Job with Multiple Volume Types

```hcl
module "complex_job" {
  source = "./modules/cloudrun-job"

  google_project_id     = "my-gcp-project"
  location              = "us-central1"
  name                  = "setup-job"
  image_url             = "us-docker.pkg.dev/my-project/repo/app:latest"
  service_account_email = "app-sa@my-project.iam.gserviceaccount.com"
  command               = ["/app/setup.sh"]
  args                  = ["--initialize"]

  memory_limit = "4Gi"
  cpu_limit    = "2"

  # Multiple volume types
  volumes = {
    # Cloud SQL instance for database access
    "cloudsql" = {
      cloudsql_instances = ["my-project:us-central1:my-db"]
    }

    # Secret containing API credentials
    "api-credentials" = {
      secret_name = "api-creds-secret"
      secret_items = [
        {
          version = "latest"
          path    = "credentials.json"
        }
      ]
    }

    # Ephemeral storage for temporary files
    "temp-storage" = {
      emptydir_medium     = "Memory"
      emptydir_size_limit = "2Gi"
    }
  }

  volume_mounts = {
    "cloudsql"         = "/cloudsql"
    "api-credentials"  = "/secrets"
    "temp-storage"     = "/tmp"
  }

  env_vars = {
    "DB_SOCKET_DIR"    = "/cloudsql"
    "CREDENTIALS_PATH" = "/secrets/credentials.json"
    "TEMP_DIR"         = "/tmp"
  }

  secret_env_vars = {
    "DB_PASSWORD" = {
      secret_id = "database-password"
    }
  }
}
```

## Important Notes

### Deletion Protection

The Cloud Run Job is created with `deletion_protection = false`, allowing Terraform to destroy the resource. If you need deletion protection for production workloads, consider modifying the module to make this configurable.

### Service Account Permissions

The service account used by the job must have appropriate IAM permissions for:

- Accessing Cloud SQL instances (if using Cloud SQL volumes)
- Reading from GCS buckets (if using GCS volumes)
- Accessing Secret Manager secrets (if using secret volumes or secret environment variables)
- Any other GCP resources the job needs to interact with

### API Enablement

The module automatically enables the Cloud Run API (`run.googleapis.com`) in the specified project. The API is not disabled when the module is destroyed (`disable_on_destroy = false`) to prevent breaking other services that may depend on it.

### Volume Mount Requirements

When using volumes, ensure that:

- The volume name in `volumes` matches the key used in `volume_mounts`
- Mount paths do not conflict with system paths
- The service account has necessary permissions to access the volume source (Cloud SQL, GCS, Secrets)

### Retry Behavior

The `max_retries` setting controls how many times Cloud Run will retry a failed job execution. Set to `0` for no retries, which is useful for jobs that should only run once or have their own internal retry logic.

### Resource Limits

Cloud Run Jobs have specific limits on CPU and memory combinations. Refer to [Cloud Run quotas and limits](https://cloud.google.com/run/quotas) for valid configurations.

## Terraform State Considerations

### Non-Destructive Changes

The following changes can be applied without destroying the job:

- Modifying environment variables
- Updating container image URL
- Changing resource limits
- Adjusting max retries

### Potentially Destructive Changes

Some changes may force replacement of the Cloud Run Job:

- Changing the job name
- Modifying the project or location

Always run `terraform plan` to review changes before applying.

## Dependencies

This module depends on:

- The Google Cloud Platform provider
- Cloud Run API being available in your project (automatically enabled by the module)
- A pre-existing service account (must be created separately)
- Pre-existing secrets if using `secret_env_vars` or secret volumes
- Pre-existing GCS buckets if using GCS volumes
- Pre-existing Cloud SQL instances if using Cloud SQL volumes

## License

This module is part of the text-diagrams infrastructure.
