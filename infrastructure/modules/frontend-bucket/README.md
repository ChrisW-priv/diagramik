# Frontend Bucket Module

This Terraform module provisions a Google Cloud Storage (GCS) bucket configured for static website hosting with public read access. It is designed to host frontend applications and static assets, making them accessible via HTTP/HTTPS through GCS website hosting or a load balancer.

## Overview

The module creates the following GCP resources:

- **Google Cloud Storage API Enablement**: Ensures the Cloud Storage API is enabled for the project
- **GCS Bucket**: A storage bucket configured with:
  - Uniform bucket-level access for simplified permissions management
  - Website configuration with customizable index and error pages
  - STANDARD storage class for optimal performance
- **Public Read IAM Policy**: Grants public read access to all objects in the bucket via the `allUsers` member

## Architecture

```
┌─────────────────────────────────────────┐
│  Google Project                         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ Storage API (enabled)             │ │
│  └───────────────────────────────────┘ │
│              │                          │
│              │ depends_on               │
│              ▼                          │
│  ┌───────────────────────────────────┐ │
│  │ GCS Bucket                        │ │
│  │  - ${application_name}-frontend   │ │
│  │  - Website hosting enabled        │ │
│  │  - Uniform bucket-level access    │ │
│  └───────────────────────────────────┘ │
│              │                          │
│              │ IAM binding              │
│              ▼                          │
│  ┌───────────────────────────────────┐ │
│  │ Public Read Access                │ │
│  │  - roles/storage.objectViewer     │ │
│  │  - member: allUsers               │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Requirements

| Name      | Version |
| --------- | ------- |
| terraform | >= 1.0  |
| google    | >= 5.0  |

## Variables

### Required Variables

| Name                | Type     | Description                                                     |
| ------------------- | -------- | --------------------------------------------------------------- |
| `google_project_id` | `string` | The GCP project ID where resources will be created              |
| `location`          | `string` | The GCS bucket location (e.g., `US`, `EU`, `us-central1`)       |
| `application_name`  | `string` | The name of the application, used as prefix for the bucket name |

### Optional Variables

| Name         | Type     | Default        | Description                                                                          |
| ------------ | -------- | -------------- | ------------------------------------------------------------------------------------ |
| `index_page` | `string` | `"index.html"` | The index page for the website, served when accessing the bucket root or directories |
| `error_page` | `string` | `"404.html"`   | The error page displayed for 404 Not Found errors                                    |

### Variable Details

**`google_project_id`**

- The GCP project identifier where the bucket will be created
- Must be a valid, existing GCP project ID
- The project must have billing enabled

**`location`**

- Determines the geographic location of the bucket
- Can be a multi-region (`US`, `EU`, `ASIA`) or single region (`us-central1`, `europe-west1`, etc.)
- Multi-region provides higher availability; single region provides lower latency for specific locations
- See [GCP Bucket Locations](https://cloud.google.com/storage/docs/locations) for available options

**`application_name`**

- Used to construct the bucket name as `${application_name}-frontend`
- Must be globally unique across all GCS buckets
- Should follow DNS naming conventions (lowercase letters, numbers, hyphens)
- Cannot contain underscores or special characters

**`index_page`**

- The file served when accessing the bucket or a directory without specifying a filename
- Typically `index.html` for web applications
- File must exist in the bucket for website hosting to work correctly

**`error_page`**

- The file served when a requested object is not found (HTTP 404)
- Typically `404.html` for custom error pages
- File must exist in the bucket or GCS will serve a default error page

## Outputs

| Name          | Description                                                                      |
| ------------- | -------------------------------------------------------------------------------- |
| `bucket_name` | The name of the created frontend bucket (format: `${application_name}-frontend`) |

### Output Usage

The `bucket_name` output can be used to:

- Configure load balancers or CDN backends
- Reference the bucket in CI/CD pipelines for deployment
- Create IAM bindings for service accounts
- Configure Cloud Build triggers for automated deployments

## Usage Examples

### Basic Usage

```hcl
module "frontend_bucket" {
  source = "./modules/frontend-bucket"

  google_project_id = "my-gcp-project"
  location          = "US"
  application_name  = "my-app"
}
```

This creates a bucket named `my-app-frontend` in the `US` multi-region with default index and error pages.

### Custom Website Configuration

```hcl
module "frontend_bucket" {
  source = "./modules/frontend-bucket"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  application_name  = "my-app"
  index_page        = "home.html"
  error_page        = "error.html"
}
```

### Integration with Load Balancer

```hcl
module "frontend_bucket" {
  source = "./modules/frontend-bucket"

  google_project_id = var.google_project_id
  location          = var.google_region
  application_name  = var.application_name
}

module "load_balancer" {
  source = "./modules/global-lb"

  google_project_id    = var.google_project_id
  application_name     = var.application_name
  frontend_bucket_name = module.frontend_bucket.bucket_name
  # ... other load balancer configuration
}
```

### Multi-Environment Setup

```hcl
module "frontend_bucket_dev" {
  source = "./modules/frontend-bucket"

  google_project_id = "my-project-dev"
  location          = "us-central1"
  application_name  = "my-app-dev"
}

module "frontend_bucket_prod" {
  source = "./modules/frontend-bucket"

  google_project_id = "my-project-prod"
  location          = "US"  # Multi-region for production
  application_name  = "my-app-prod"
}
```

## Important Notes

### Security Considerations

**Public Access**: This module intentionally grants public read access to all objects in the bucket via the `allUsers` IAM member. This is suitable for hosting public static websites but should NOT be used for:

- Storing sensitive data
- Private applications requiring authentication
- User-uploaded content that should be access-controlled

**Uniform Bucket-Level Access**: The module enforces uniform bucket-level access, which means:

- All permissions are managed at the bucket level via IAM
- Individual object ACLs are disabled
- This simplifies permission management and aligns with GCP security best practices

### Deployment Workflow

After provisioning this bucket, you'll need to:

1. **Upload Files**: Deploy your static assets to the bucket

   ```bash
   gsutil -m rsync -r ./dist gs://my-app-frontend
   ```

1. **Configure Load Balancer**: If using a load balancer (recommended for production), configure it to use this bucket as a backend

1. **Verify Website Configuration**: Ensure `index.html` and `404.html` (or your custom pages) exist in the bucket

### State Impact

**Initial Creation**: Creates all resources from scratch with no state dependencies.

**Bucket Name Changes**: Changing `application_name` will force bucket recreation:

- **Data Loss Risk**: Recreating the bucket will delete all existing objects
- **Mitigation**: Use `terraform import` to import existing buckets or perform manual migration

**Location Changes**: Changing `location` requires bucket recreation:

- GCS buckets cannot have their location changed after creation
- Plan for data migration before applying location changes

### Limitations

- **Bucket Naming**: Bucket names must be globally unique across all GCS buckets worldwide
- **No HTTPS Direct**: GCS website hosting serves content over HTTP only; use Cloud Load Balancing for HTTPS
- **No Custom Domain**: Direct custom domain mapping requires domain verification; use Cloud Load Balancing for custom domains
- **API Dependency**: The module explicitly enables the Storage API, which may take a few moments on first run

### Cost Considerations

- **Storage Class**: Uses STANDARD storage class, which is more expensive than NEARLINE, COLDLINE, or ARCHIVE but provides optimal performance for frequently accessed content
- **Network Egress**: Public internet egress from GCS incurs charges; consider using Cloud CDN to reduce costs
- **API Requests**: Each file access incurs a Class A or Class B operation charge

## Troubleshooting

### Bucket Name Already Exists

**Error**: `Error creating bucket: googleapi: Error 409: You already own this bucket`

**Solution**: The bucket name must be globally unique. Change the `application_name` variable to use a different prefix.

### Storage API Not Enabled

**Error**: `Error 403: Cloud Storage API has not been used in project`

**Solution**: The module handles this automatically via the `google_project_service` resource. If this error persists, manually enable the API or check project permissions.

### Website Not Serving Correctly

**Issue**: Accessing the bucket returns errors or doesn't serve the index page.

**Solutions**:

- Ensure `index.html` and `404.html` exist in the bucket root
- Verify objects have public read access (module handles this automatically)
- Check that objects are uploaded with appropriate content types
- For HTTPS access, configure a load balancer; direct GCS website hosting uses HTTP only

## Related Modules

This module is typically used alongside:

- `global-lb`: Provides HTTPS, custom domain support, and CDN capabilities
- `django-monolith`: Backend API services that complement the static frontend
- `mcp-service`: Additional backend services

## License

This module is part of the text-diagrams project infrastructure.
