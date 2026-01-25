# GCP Artifact Registry Module

This Terraform module provisions a Google Cloud Artifact Registry repository for Docker container images with automated cleanup policies and IAM access controls.

## Overview

This module creates and configures:

- **GCP Artifact Registry API enablement**: Ensures the Artifact Registry API is enabled in the target project
- **Docker Artifact Registry repository**: A dedicated repository for storing Docker container images
- **Cleanup policies**: Automatically manages image retention by keeping a configurable number of recent versions
- **IAM access controls**: Granular read and write permissions for specified IAM members

The module implements a cleanup policy that retains the most recent N versions of each image while allowing older versions to be automatically cleaned up, helping to manage storage costs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GCP Project                                                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Artifact Registry API                                 │ │
│  │  (artifactregistry.googleapis.com)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Docker Repository                                     │ │
│  │  - Format: DOCKER                                      │ │
│  │  - Cleanup: Keep N recent versions                     │ │
│  │  - Location: Configurable region                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│         ┌─────────────────┴─────────────────┐               │
│         ▼                                   ▼               │
│  ┌─────────────┐                     ┌─────────────┐        │
│  │ IAM Readers │                     │ IAM Writers │        │
│  │ (Read Only) │                     │ (Read/Write)│        │
│  └─────────────┘                     └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- **Terraform**: >= 0.13
- **Provider**: `google` (hashicorp/google)
- **GCP Permissions**: The service account or user running Terraform must have:
  - `roles/serviceusage.serviceUsageAdmin` (to enable APIs)
  - `roles/artifactregistry.admin` (to create and manage repositories)
  - `roles/resourcemanager.projectIamAdmin` (to manage IAM bindings)

## Variables

### Required Variables

| Name                | Type     | Description                                                                                            |
| ------------------- | -------- | ------------------------------------------------------------------------------------------------------ |
| `google_project_id` | `string` | The GCP project ID where the Artifact Registry repository will be created                              |
| `location`          | `string` | The GCP region or multi-region location for the repository (e.g., `us-central1`, `us`, `europe-west1`) |
| `repository_id`     | `string` | The unique identifier for the repository. Must be lowercase, alphanumeric, and may contain hyphens     |

### Optional Variables

| Name          | Type           | Default                     | Description                                                                                                                                                    |
| ------------- | -------------- | --------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `description` | `string`       | `"Docker container images"` | Human-readable description of the repository                                                                                                                   |
| `keep_count`  | `number`       | `10`                        | Number of most recent image versions to retain per image. Older versions will be eligible for cleanup                                                          |
| `readers`     | `list(string)` | `[]`                        | List of IAM members granted read-only access. Format: `user:email@example.com`, `serviceAccount:sa@project.iam.gserviceaccount.com`, `group:group@example.com` |
| `writers`     | `list(string)` | `[]`                        | List of IAM members granted read and write access. Format: same as `readers`                                                                                   |

### Variable Usage Notes

- **location**: Choose a location based on your latency requirements and data residency policies. Multi-region locations (`us`, `europe`, `asia`) provide higher availability but may have higher costs.
- **keep_count**: Set this based on your rollback requirements and storage budget. Lower values reduce storage costs but limit rollback options.
- **readers/writers**: IAM members must be in the correct format. Writers automatically receive read permissions. The module uses `for_each` to create individual IAM bindings for each member, allowing granular management.

## Outputs

| Name             | Description                                           | Example Value                                                          |
| ---------------- | ----------------------------------------------------- | ---------------------------------------------------------------------- |
| `repository_id`  | The repository ID (same as input)                     | `my-app-images`                                                        |
| `repository_url` | The full Docker registry URL for push/pull operations | `us-central1-docker.pkg.dev/my-project/my-app-images`                  |
| `name`           | The fully qualified resource name                     | `projects/my-project/locations/us-central1/repositories/my-app-images` |

### Output Usage

The `repository_url` output is particularly useful for:

- Configuring Docker CLI authentication: `docker tag myimage:latest ${repository_url}/myimage:latest`
- CI/CD pipeline configurations
- Application deployment manifests that pull images from the registry

## Usage Examples

### Basic Usage

```hcl
module "artifact_registry" {
  source = "./modules/artifact-registry"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  repository_id     = "my-app-images"
}
```

### Advanced Usage with IAM and Custom Retention

```hcl
module "artifact_registry" {
  source = "./modules/artifact-registry"

  google_project_id = "my-gcp-project"
  location          = "us-central1"
  repository_id     = "production-images"
  description       = "Production Docker images for microservices"
  keep_count        = 20  # Keep 20 versions for extended rollback capability

  # Grant read access to production service accounts
  readers = [
    "serviceAccount:gke-node-sa@my-gcp-project.iam.gserviceaccount.com",
    "serviceAccount:cloud-run-sa@my-gcp-project.iam.gserviceaccount.com",
  ]

  # Grant write access to CI/CD service accounts
  writers = [
    "serviceAccount:github-actions@my-gcp-project.iam.gserviceaccount.com",
    "serviceAccount:cloudbuild@my-gcp-project.iam.gserviceaccount.com",
  ]
}

# Use the output in other resources
output "docker_registry_url" {
  description = "Docker registry URL for CI/CD pipelines"
  value       = module.artifact_registry.repository_url
}
```

### Multi-Region Setup

```hcl
module "artifact_registry_us" {
  source = "./modules/artifact-registry"

  google_project_id = "my-gcp-project"
  location          = "us"  # Multi-region
  repository_id     = "global-images"
  description       = "Globally replicated container images"
  keep_count        = 15

  readers = [
    "serviceAccount:prod-workload@my-gcp-project.iam.gserviceaccount.com",
  ]

  writers = [
    "serviceAccount:ci-cd@my-gcp-project.iam.gserviceaccount.com",
  ]
}
```

### Using with Docker Push/Pull

After applying the module, authenticate and use the repository:

```bash
# Authenticate Docker with GCP
gcloud auth configure-docker us-central1-docker.pkg.dev

# Tag your image
docker tag myapp:latest us-central1-docker.pkg.dev/my-gcp-project/my-app-images/myapp:latest

# Push to the registry
docker push us-central1-docker.pkg.dev/my-gcp-project/my-app-images/myapp:latest

# Pull from the registry
docker pull us-central1-docker.pkg.dev/my-gcp-project/my-app-images/myapp:latest
```

## Important Notes

### Cleanup Policy Behavior

- The cleanup policy uses `cleanup_policy_dry_run = false`, meaning it will actively delete images that exceed the `keep_count` threshold.
- The policy is set to `KEEP` the most recent N versions, not delete them. Older versions beyond this count will be automatically removed.
- Cleanup runs periodically (GCP-managed schedule), not immediately after each push.
- All tags pointing to a version count toward retention; untagged versions may be cleaned up more aggressively.

### IAM Permissions

- **Reader role** (`roles/artifactregistry.reader`): Can pull images and view repository metadata
- **Writer role** (`roles/artifactregistry.writer`): Can pull and push images, but cannot modify repository settings
- The module creates individual IAM bindings per member using `for_each`, which provides better state management compared to authoritative bindings.

### State Impact Considerations

- **Destroying the repository**: Will permanently delete all images. The repository itself is not protected by `prevent_destroy` lifecycle rules.
- **API enablement**: The Artifact Registry API has `disable_on_destroy = false`, meaning it will remain enabled even if the module is destroyed. This prevents accidental API disablement that could affect other repositories.
- **Changing repository_id**: Forces recreation of the repository and all IAM bindings, resulting in data loss. Use `terraform state mv` if renaming is required.
- **Modifying IAM lists**: Adding/removing members from `readers` or `writers` will only affect those specific bindings due to the `for_each` implementation.

### Dependencies

The module implements an explicit dependency chain:

```
google_project_service.artifactregistry
         ↓
google_artifact_registry_repository.repo
         ↓
google_artifact_registry_repository_iam_member.*
```

This ensures the API is enabled before the repository is created, and the repository exists before IAM bindings are applied.

## Security Considerations

1. **Least Privilege**: Only grant `writers` access to service accounts that need to push images (CI/CD systems). Application workloads should only have `readers` access.

1. **Service Account Keys**: Avoid using service account keys for authentication when possible. Use Workload Identity for GKE or service account impersonation for Cloud Build.

1. **Vulnerability Scanning**: Consider enabling GCP's Container Analysis API for automatic vulnerability scanning of images stored in the registry.

1. **Network Security**: For highly sensitive workloads, consider using VPC Service Controls to restrict access to the Artifact Registry from specific networks.

## Limitations

- **Format**: This module is hardcoded to Docker format. For other formats (Maven, npm, Python, etc.), the module would need modification.
- **Cleanup Policies**: Only implements version-based cleanup. Time-based or tag-based cleanup policies are not supported.
- **Repository Immutability**: The module does not configure repository immutability settings.
- **Customer Managed Encryption Keys (CMEK)**: The module uses Google-managed encryption keys. CMEK support is not implemented.

## License

This module is part of the text-diagrams project infrastructure.
