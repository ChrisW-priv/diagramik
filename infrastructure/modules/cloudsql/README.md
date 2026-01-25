# CloudSQL Terraform Module

This Terraform module provisions a Google Cloud SQL PostgreSQL instance with automated password management through Secret Manager.

## Overview

This module creates and manages the following GCP resources:

- **Cloud SQL PostgreSQL Instance**: A managed PostgreSQL database instance
- **Cloud SQL Admin User**: Database user with administrative privileges
- **Secret Manager Secret**: Automatically generated database password stored securely
- **Required APIs**: Enables the Cloud SQL Admin API (`sqladmin.googleapis.com`)

The module automatically generates a secure random password for the database admin user and stores it in Google Secret Manager, eliminating the need to manage database credentials manually.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ CloudSQL Module                                         │
│                                                         │
│  ┌──────────────────────────────────────┐              │
│  │ google_sql_database_instance         │              │
│  │ - PostgreSQL Database                │              │
│  │ - Configurable tier & version        │              │
│  └──────────────┬───────────────────────┘              │
│                 │                                       │
│                 │ connects to                           │
│                 ▼                                       │
│  ┌──────────────────────────────────────┐              │
│  │ google_sql_user (admin)              │              │
│  │ - Username: configurable             │              │
│  │ - Password: from Secret Manager      │◄─────────┐   │
│  └──────────────────────────────────────┘          │   │
│                                                     │   │
│  ┌──────────────────────────────────────┐          │   │
│  │ Secret Module (nested)               │          │   │
│  │ - Generates random password          │──────────┘   │
│  │ - Stores in Secret Manager           │              │
│  │ - Secret: DJANGO_MONOLITH_POSTGRES_  │              │
│  │           DB_PASSWORD                │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Requirements

- **Terraform**: >= 0.13
- **Provider**: `google` (hashicorp/google)
- **GCP APIs**: The module enables `sqladmin.googleapis.com` automatically
- **IAM Permissions**: The executing identity needs:
  - `cloudsql.instances.create`
  - `cloudsql.users.create`
  - `secretmanager.secrets.create`
  - `serviceusage.services.enable`

## Dependencies

This module depends on the `../secret` module for password generation and Secret Manager integration.

## Variables

### Required Variables

| Name                | Description                                        | Type     |
| ------------------- | -------------------------------------------------- | -------- |
| `google_project_id` | The GCP project ID where resources will be created | `string` |
| `google_region`     | The GCP region for the Cloud SQL instance          | `string` |
| `instance_name`     | The name of the Cloud SQL instance                 | `string` |

### Optional Variables

| Name               | Description                                            | Type     | Default         |
| ------------------ | ------------------------------------------------------ | -------- | --------------- |
| `instance_tier`    | The machine type for the Cloud SQL instance            | `string` | `"db-f1-micro"` |
| `db_user`          | The username for the PostgreSQL database admin user    | `string` | `"postgres"`    |
| `database_name`    | The name of the database to create within the instance | `string` | `"postgres"`    |
| `database_version` | The version of PostgreSQL to use                       | `string` | `"POSTGRES_15"` |

### Variable Details

#### `instance_tier`

The machine type determines the CPU and memory resources for your database. Common values:

- `db-f1-micro`: Shared-core, 0.6GB RAM (suitable for development)
- `db-g1-small`: Shared-core, 1.7GB RAM
- `db-n1-standard-1`: 1 vCPU, 3.75GB RAM
- `db-n1-standard-2`: 2 vCPU, 7.5GB RAM

See [Cloud SQL pricing](https://cloud.google.com/sql/pricing) for complete list.

#### `database_version`

Supported PostgreSQL versions include:

- `POSTGRES_15` (default)
- `POSTGRES_14`
- `POSTGRES_13`
- `POSTGRES_12`

Note: The module currently does not create a database within the instance. The `database_name` variable is exposed for future use or manual database creation.

## Outputs

| Name                    | Description                                                                              | Type     |
| ----------------------- | ---------------------------------------------------------------------------------------- | -------- |
| `instance`              | The Cloud SQL instance connection name (same as `connection_name`)                       | `string` |
| `connection_name`       | The connection name in format `project:region:instance-name` for connecting applications | `string` |
| `instance_name`         | The name of the Cloud SQL instance                                                       | `string` |
| `db_admin_user`         | The username for the PostgreSQL database admin user                                      | `string` |
| `db_password_secret_id` | The Secret Manager secret ID containing the database password                            | `string` |
| `db_name`               | The configured database name (note: database is not automatically created)               | `string` |

### Output Usage

The `connection_name` output is critical for connecting to Cloud SQL from GCP services like Cloud Run:

```hcl
# Use in Cloud Run volume mount
volumes {
  name = "cloudsql"
  cloud_sql_instance {
    instances = [module.postgres_db.connection_name]
  }
}
```

The `db_password_secret_id` can be used to grant IAM access to the password:

```hcl
resource "google_secret_manager_secret_iam_member" "app_access" {
  secret_id = module.postgres_db.db_password_secret_id
  member    = "serviceAccount:${var.service_account_email}"
  role      = "roles/secretmanager.secretAccessor"
}
```

## Usage Examples

### Basic Usage

```hcl
module "postgres_db" {
  source = "./modules/cloudsql"

  google_project_id = "my-gcp-project"
  google_region     = "us-central1"
  instance_name     = "my-app-postgres"
}

# Access the connection details
output "db_connection" {
  value = module.postgres_db.connection_name
}

output "db_password_secret" {
  value     = module.postgres_db.db_password_secret_id
  sensitive = true
}
```

### Production Configuration

```hcl
module "postgres_db" {
  source = "./modules/cloudsql"

  google_project_id = "production-project"
  google_region     = "us-east1"
  instance_name     = "production-postgres"

  # Production-grade instance
  instance_tier    = "db-n1-standard-2"
  database_version = "POSTGRES_15"

  # Custom admin user
  db_user       = "app_admin"
  database_name = "application_db"
}
```

### Integration with Cloud Run

This example shows how to use the CloudSQL module with a Cloud Run service:

```hcl
# Create the database
module "postgres_db" {
  source = "./modules/cloudsql"

  google_project_id = var.project_id
  google_region     = var.region
  instance_name     = "django-monolith-postgres"
}

# Create a service account for Cloud Run
resource "google_service_account" "app_sa" {
  account_id   = "app-service-account"
  display_name = "Application Service Account"
}

# Grant Cloud SQL client role
resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = google_service_account.app_sa.member
}

# Grant access to database password secret
resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = module.postgres_db.db_password_secret_id
  member    = google_service_account.app_sa.member
  role      = "roles/secretmanager.secretAccessor"
}

# Deploy Cloud Run service with database connection
resource "google_cloud_run_v2_service" "app" {
  name     = "my-app"
  location = var.region

  template {
    service_account = google_service_account.app_sa.email

    # Mount Cloud SQL instance
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [module.postgres_db.connection_name]
      }
    }

    containers {
      image = "gcr.io/my-project/my-app:latest"

      # Mount the Cloud SQL volume
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      # Database connection environment variables
      env {
        name  = "DB_CONN_NAME"
        value = module.postgres_db.connection_name
      }

      env {
        name  = "POSTGRES_DATABASE_NAME"
        value = module.postgres_db.db_name
      }

      env {
        name  = "POSTGRES_USER"
        value = module.postgres_db.db_admin_user
      }

      # Password from Secret Manager
      env {
        name = "POSTGRES_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = module.postgres_db.db_password_secret_id
            version = "latest"
          }
        }
      }
    }
  }
}
```

## Important Notes

### Password Management

- The database password is automatically generated using a cryptographically secure random string (32 characters, alphanumeric only)
- The password is stored in Secret Manager with the ID: `DJANGO_MONOLITH_POSTGRES_DB_PASSWORD`
- The password secret is created in the same region as the Cloud SQL instance using user-managed replication
- Access to the password requires the `roles/secretmanager.secretAccessor` IAM role

### Database Creation

Important: This module creates a Cloud SQL **instance** but does not automatically create a database within that instance. The `database_name` variable is provided as an output for use in connection strings, but you must create the database manually or through application initialization scripts.

To create the database, you can:

1. Use Cloud SQL Admin UI
1. Execute SQL through the Cloud SQL Proxy:
   ```bash
   gcloud sql connect INSTANCE_NAME --user=postgres
   CREATE DATABASE your_database_name;
   ```
1. Use initialization scripts in your application (e.g., Django migrations)

### Networking and Connectivity

- This module creates a Cloud SQL instance with default networking (public IP)
- For private IP connectivity, additional VPC and networking configuration is required
- Applications running in Cloud Run should use the Cloud SQL Proxy by mounting the instance via volume configuration
- The connection name format is: `PROJECT_ID:REGION:INSTANCE_NAME`

### Security Considerations

- The Cloud SQL instance is created with default security settings
- Consider implementing additional security measures for production:
  - Enable SSL/TLS for connections
  - Configure authorized networks if using public IP
  - Use VPC-native Cloud SQL with Private IP
  - Enable Cloud SQL audit logging
  - Implement database-level access controls beyond the admin user

### Cost Optimization

- The default `db-f1-micro` tier is suitable for development but may not provide adequate performance for production
- Cloud SQL instances incur charges even when idle
- Consider enabling automatic backups and point-in-time recovery for production instances
- Review [Cloud SQL pricing documentation](https://cloud.google.com/sql/pricing) for cost estimates

### API Enablement

The module automatically enables `sqladmin.googleapis.com` with `disable_on_destroy = false`, meaning the API will remain enabled even if the module is destroyed. This prevents accidental service disruption for other Cloud SQL resources in the project.

## Lifecycle Considerations

### Updates and Modifications

- Changing `instance_name` will **destroy and recreate** the Cloud SQL instance, resulting in data loss
- Changing `database_version` may require careful planning and potential downtime
- Changing `instance_tier` typically can be done without downtime but may cause a brief restart
- The `depends_on` relationship ensures the API is enabled before instance creation

### Deletion

When destroying this module:

- The Cloud SQL instance will be deleted (use Cloud SQL's deletion protection for production)
- The Secret Manager secret containing the password will be deleted
- Deleted secrets enter a soft-delete state and can be recovered within 30 days
- The Cloud SQL Admin API will remain enabled in the project

## Troubleshooting

### Common Issues

**Issue**: Cloud Run cannot connect to Cloud SQL

- Verify the service account has `roles/cloudsql.client` role
- Ensure the Cloud SQL instance is mounted as a volume in Cloud Run
- Check that the connection name format is correct: `PROJECT:REGION:INSTANCE`

**Issue**: Cannot access database password

- Verify IAM permissions for `roles/secretmanager.secretAccessor`
- Check the secret exists: `gcloud secrets describe DJANGO_MONOLITH_POSTGRES_DB_PASSWORD`

**Issue**: Database does not exist error

- Remember: the module creates the instance but not the database
- Create the database manually or through application setup scripts

## Related Modules

- `../secret`: Used internally for password generation and Secret Manager management
- `../cloudrun-service`: Often used together for deploying applications that need database access
- `../cloudrun-job`: Useful for running database migrations or setup tasks

## Version History

This module is designed for Google Cloud Provider version 4.x and later. Ensure your Terraform configuration specifies compatible provider versions.

## Support

For issues related to:

- Cloud SQL configuration: See [Cloud SQL documentation](https://cloud.google.com/sql/docs)
- Terraform Google Provider: See [provider documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Module-specific issues: Contact your infrastructure team or module maintainer
