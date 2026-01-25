# GCP Storage Bucket Module

This Terraform module provisions a Google Cloud Storage bucket with configurable IAM permissions and bucket-level access controls.

## Overview

This module creates:

- A Google Cloud Storage bucket with customizable configuration
- IAM member bindings for granular access control
- Automatic enablement of the Cloud Storage API service

The module handles the complexity of setting up bucket-level IAM permissions using a user-friendly list of permission objects, internally converting them to the map structure required by Terraform's `for_each` meta-argument.

## Requirements

- Terraform >= 0.13
- Google Cloud Provider
- Appropriate GCP project permissions to:
  - Enable APIs (`serviceusage.services.enable`)
  - Create storage buckets (`storage.buckets.create`)
  - Manage IAM policies (`storage.buckets.setIamPolicy`)

## Resources Created

| Resource Type                      | Description                           |
| ---------------------------------- | ------------------------------------- |
| `google_project_service`           | Enables the Cloud Storage API         |
| `google_storage_bucket`            | The GCS bucket itself                 |
| `google_storage_bucket_iam_member` | IAM member bindings for bucket access |

## Resource Dependencies

The module implements explicit dependencies to ensure proper resource creation order:

1. Cloud Storage API service is enabled first
1. Storage bucket is created after API enablement
1. IAM permissions are applied after bucket creation

## Variables

### Required Variables

| Variable            | Type           | Description                                                                  |
| ------------------- | -------------- | ---------------------------------------------------------------------------- |
| `google_project_id` | `string`       | The GCP project ID where resources will be created                           |
| `location`          | `string`       | The location/region for the storage bucket (e.g., `us-central1`, `US`, `EU`) |
| `name`              | `string`       | The globally unique name for the storage bucket                              |
| `permissions`       | `list(object)` | List of IAM permission objects (see structure below)                         |

#### Permissions Structure

The `permissions` variable expects a list of objects with the following structure:

```hcl
permissions = [
  {
    member = "user:email@example.com"  # or "allUsers", "serviceAccount:...", etc.
    role   = "roles/storage.objectViewer"
  }
]
```

### Optional Variables

| Variable                      | Type     | Default      | Description                                                                                          |
| ----------------------------- | -------- | ------------ | ---------------------------------------------------------------------------------------------------- |
| `storage_class`               | `string` | `"STANDARD"` | Storage class for the bucket. Options: `STANDARD`, `NEARLINE`, `COLDLINE`, `ARCHIVE`                 |
| `force_destroy`               | `bool`   | `false`      | If true, allows deletion of bucket even when it contains objects. **Use with caution in production** |
| `uniform_bucket_level_access` | `bool`   | `true`       | Enables uniform bucket-level access, which disables object-level ACLs                                |

## Outputs

| Output | Description                            |
| ------ | -------------------------------------- |
| `name` | The name of the created storage bucket |

## Usage Examples

### Basic Usage

```hcl
module "storage_bucket" {
  source = "./modules/storage-bucket"

  google_project_id = "my-gcp-project"
  name              = "my-unique-bucket-name"
  location          = "us-central1"

  permissions = [
    {
      member = "serviceAccount:my-service@my-project.iam.gserviceaccount.com"
      role   = "roles/storage.objectAdmin"
    }
  ]
}
```

### Public Website Hosting

```hcl
module "public_website_bucket" {
  source = "./modules/storage-bucket"

  google_project_id = "my-gcp-project"
  name              = "my-website-bucket"
  location          = "US"
  storage_class     = "STANDARD"

  permissions = [
    {
      member = "allUsers"
      role   = "roles/storage.objectViewer"
    }
  ]
}
```

### Multi-Region Archive Storage

```hcl
module "archive_bucket" {
  source = "./modules/storage-bucket"

  google_project_id = "my-gcp-project"
  name              = "my-archive-bucket"
  location          = "EU"
  storage_class     = "ARCHIVE"
  force_destroy     = false

  permissions = [
    {
      member = "group:data-team@example.com"
      role   = "roles/storage.objectViewer"
    },
    {
      member = "serviceAccount:backup-service@my-project.iam.gserviceaccount.com"
      role   = "roles/storage.objectCreator"
    }
  ]
}
```

### Development Bucket with Force Destroy

```hcl
module "dev_bucket" {
  source = "./modules/storage-bucket"

  google_project_id = "my-dev-project"
  name              = "dev-test-bucket"
  location          = "us-west1"
  force_destroy     = true  # Safe for dev/test environments

  permissions = [
    {
      member = "serviceAccount:ci-cd@my-project.iam.gserviceaccount.com"
      role   = "roles/storage.admin"
    }
  ]
}

output "bucket_name" {
  value = module.dev_bucket.name
}
```

## Important Notes

### Bucket Naming

- Bucket names must be globally unique across all GCP projects
- Names must be 3-63 characters long
- Only lowercase letters, numbers, hyphens, and underscores are allowed
- Names cannot begin or end with a hyphen

### Storage Classes

Choose the appropriate storage class based on access patterns:

- **STANDARD**: Frequently accessed data
- **NEARLINE**: Data accessed less than once per month
- **COLDLINE**: Data accessed less than once per quarter
- **ARCHIVE**: Data accessed less than once per year

### Force Destroy Warning

Setting `force_destroy = true` allows Terraform to delete the bucket and all its contents during `terraform destroy`. This is convenient for development but **dangerous in production**. Consider:

- Keeping `force_destroy = false` for production buckets
- Using lifecycle policies for data retention
- Implementing backup strategies before enabling force destroy

### Uniform Bucket-Level Access

The module defaults to `uniform_bucket_level_access = true`, which:

- Simplifies IAM management by using only bucket-level permissions
- Disables legacy object-level ACLs
- Is recommended for new buckets per Google Cloud best practices
- Cannot be enabled if object ACLs are in use (requires 90-day waiting period to re-enable)

### IAM Permission Types

Common IAM roles for Cloud Storage:

- `roles/storage.admin`: Full control of buckets and objects
- `roles/storage.objectAdmin`: Full control of objects only
- `roles/storage.objectCreator`: Create objects (upload)
- `roles/storage.objectViewer`: Read objects (download)
- `roles/storage.legacyBucketReader`: Read bucket metadata and list objects
- `roles/storage.legacyBucketWriter`: Read/write bucket metadata and objects

Member types:

- `allUsers`: Anyone on the internet (use for public access)
- `allAuthenticatedUsers`: Anyone with a Google account
- `user:email@example.com`: Specific user
- `serviceAccount:name@project.iam.gserviceaccount.com`: Service account
- `group:group@example.com`: Google Group
- `domain:example.com`: All users in a Google Workspace domain

## State Impact Considerations

### Destructive Operations

The following changes will **destroy and recreate** the bucket (data loss risk):

- Changing the `name` variable
- Changing the `location` variable

These operations will destroy all bucket contents unless they are backed up or migrated.

### Safe Modifications

The following changes can be applied without recreating the bucket:

- Adding or removing items from `permissions`
- Changing `storage_class` (subject to GCP restrictions)
- Toggling `force_destroy`
- Toggling `uniform_bucket_level_access` (subject to 90-day lock period)

### API Enablement

The module automatically enables the Cloud Storage API (`storage.googleapis.com`). The API will remain enabled even after destroying the module (`disable_on_destroy = false`) to prevent accidental service disruption.

## Migration and Lifecycle

### Moving Existing Buckets

If you need to import an existing bucket into this module:

```bash
terraform import module.storage_bucket.google_storage_bucket.bucket <bucket-name>
```

### Preventing Accidental Deletion

To add an extra layer of protection, consider adding a lifecycle rule to the bucket resource:

```hcl
# In main.tf (requires module modification)
lifecycle {
  prevent_destroy = true
}
```

## Troubleshooting

### Bucket Already Exists Error

If you receive an error that the bucket name already exists:

- Bucket names are globally unique across all GCP projects
- Choose a different name
- If you own the bucket in another project, consider importing it or deleting it first

### Permission Denied Errors

Ensure the Terraform service account or user has:

- `roles/serviceusage.serviceUsageAdmin` (to enable APIs)
- `roles/storage.admin` (to create buckets and manage IAM)

### API Not Enabled

The module handles API enablement automatically, but there may be a brief delay (5-30 seconds) after enabling. If you encounter API-not-enabled errors, the explicit `depends_on` should resolve this, but you may need to retry the apply.

## License

This module is part of the text-diagrams project.
