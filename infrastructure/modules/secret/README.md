# GCP Secret Manager Module

## Overview

This Terraform module provisions and manages secrets in Google Cloud Platform's Secret Manager service. It automates the creation of secrets with proper IAM access controls and supports both user-provided secret data and auto-generated random passwords.

## Resources Created

This module creates and manages the following GCP resources:

- **google_project_service**: Enables the Secret Manager API (`secretmanager.googleapis.com`)
- **google_secret_manager_secret**: Creates a Secret Manager secret with user-managed replication
- **google_secret_manager_secret_version**: Stores the secret data (either provided or auto-generated)
- **google_secret_manager_secret_iam_member**: Grants secretAccessor role to specified members
- **random_password**: Generates a 32-character alphanumeric password if no secret data is provided

## Features

- Automatic enablement of Secret Manager API
- User-managed replication in a specified location
- Optional automatic password generation (32-character alphanumeric)
- Flexible IAM access control for multiple members
- Sensitive data handling with appropriate Terraform sensitivity flags

## Requirements

- Terraform >= 0.13
- Google Cloud Provider
- Random Provider (for password generation)
- Sufficient GCP permissions to:
  - Enable APIs on the project
  - Create and manage Secret Manager secrets
  - Manage Secret Manager IAM policies

## Variables

### Required Variables

| Name                | Type     | Description                                             |
| ------------------- | -------- | ------------------------------------------------------- |
| `google_project_id` | `string` | The GCP project ID where resources will be created      |
| `location`          | `string` | The GCP location/region for secret replication          |
| `secret_name`       | `string` | The unique identifier for the secret within the project |

### Optional Variables

| Name          | Type                 | Default | Description                                                                                                                                                        |
| ------------- | -------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `secret_data` | `string` (sensitive) | `""`    | The data to store in the secret. If empty, a random 32-character alphanumeric password will be generated                                                           |
| `members`     | `set(string)`        | `[]`    | Set of IAM members to grant `roles/secretmanager.secretAccessor` role. Format: `user:email@example.com`, `serviceAccount:sa@project.iam.gserviceaccount.com`, etc. |
| `length`      | `int`                | `32`    | Length of the randomly generated sequence                                                                                                                          |

## Outputs

| Name           | Description                                                  | Sensitive |
| -------------- | ------------------------------------------------------------ | --------- |
| `secret_id`    | The ID of the created secret (same as `secret_name`)         | No        |
| `secret_value` | The actual secret data stored (either provided or generated) | Yes       |

## Usage Examples

### Basic Usage with Auto-Generated Password

```hcl
module "database_password" {
  source = "./modules/secret"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  secret_name       = "database-password"
}

# Access the auto-generated password
output "db_password" {
  value     = module.database_password.secret_value
  sensitive = true
}
```

### Usage with User-Provided Secret Data

```hcl
module "api_key" {
  source = "./modules/secret"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  secret_name       = "external-api-key"
  secret_data       = var.api_key_value  # Provided from external source
}
```

### Usage with IAM Access Control

```hcl
module "shared_secret" {
  source = "./modules/secret"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  secret_name       = "shared-service-key"

  members = [
    "serviceAccount:backend-service@my-gcp-project.iam.gserviceaccount.com",
    "serviceAccount:worker-service@my-gcp-project.iam.gserviceaccount.com",
    "user:admin@example.com"
  ]
}
```

### Complete Example with All Options

```hcl
module "production_secret" {
  source = "./modules/secret"

  google_project_id = "my-gcp-project"
  location          = "us-east1"
  secret_name       = "prod-oauth-client-secret"
  secret_data       = var.oauth_client_secret

  members = [
    "serviceAccount:webapp@my-gcp-project.iam.gserviceaccount.com",
    "serviceAccount:api-backend@my-gcp-project.iam.gserviceaccount.com"
  ]
}
```

## Important Notes

### Replication Strategy

This module uses **user-managed replication** in a single specified location. The secret data is replicated only to the location specified in the `location` variable. If you need automatic multi-region replication, you would need to modify the `replication` block in `main.tf`.

### Auto-Generated Passwords

When `secret_data` is not provided (empty string), the module generates a random 32-character password containing:

- Uppercase and lowercase letters
- Numbers
- **No special characters** (`special = false`)

If you need special characters in auto-generated passwords, this can be modified in the `random_password` resource.

### IAM Member Format

The `members` variable accepts standard GCP IAM member identifiers:

- `user:name@example.com` - Individual user accounts
- `serviceAccount:sa-name@project-id.iam.gserviceaccount.com` - Service accounts
- `group:group@example.com` - Google Groups
- `domain:example.com` - All users in a domain

All members are granted the `roles/secretmanager.secretAccessor` role, which allows them to access secret versions.

### State File Security

Because this module handles sensitive data, ensure your Terraform state files are:

- Stored securely (e.g., encrypted GCS backend)
- Access-controlled appropriately
- Never committed to version control

### API Enablement

The module automatically enables the Secret Manager API (`secretmanager.googleapis.com`) with `disable_on_destroy = false`, meaning the API will remain enabled even if the module resources are destroyed. This prevents accidental service disruption.

### Dependencies

The module uses explicit `depends_on` to ensure proper resource creation order:

1. Secret Manager API is enabled first
1. Secret resource is created
1. Secret version with data is added
1. IAM bindings are applied

## Limitations

- Single-location replication only
- Fixed IAM role (secretAccessor) - cannot customize per member
- Auto-generated passwords are alphanumeric only (no special characters)
- API remains enabled after module destruction

## Migration Considerations

When destroying and recreating this module:

- **State Impact**: Destroying the module will delete the secret and all its versions permanently
- **No prevent_destroy**: This module does not include lifecycle protection; consider adding it for production secrets
- **Secret Rotation**: Updating `secret_data` creates a new secret version without destroying the secret itself

## Terraform State Operations

If you need to rename a secret without destroying it:

```bash
# Move state to preserve the secret
terraform state mv 'module.old_name.google_secret_manager_secret.secret' 'module.new_name.google_secret_manager_secret.secret'
```

## License

This module is part of the text-diagrams project infrastructure.
