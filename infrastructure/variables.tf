variable "google_project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "google_region" {
  description = "The GCP region"
  type        = string
  default     = "europe-west4"
}

variable "application_name" {
  description = "The name of the application"
  type        = string
  default     = "diagramik"
}

variable "docker_image_tag" {
  description = "The Docker image tag (commit SHA)"
  type        = string
  default     = "latest"
}

variable "github_repository" {
  description = "GitHub repository in 'owner/repo' format for Workload Identity Federation"
  type        = string
  default     = ""
}

variable "workload_identity_pool_id" {
  description = "The ID of the Workload Identity Pool for GitHub Actions OIDC"
  type        = string
  default     = ""
}

variable "domain" {
  description = "Primary domain for the application"
  type        = string
  default     = "diagramik.com"
}

variable "additional_domains" {
  description = "Additional domains for SSL certificate"
  type        = list(string)
  default     = ["www.diagramik.com"]
}

variable "gcs_sa_key_json" {
  description = "JSON key for GCS signed URL service account. If empty, a placeholder will be used."
  type        = string
  sensitive   = true
  default     = "{}"
}

variable "fastagent_config_yaml" {
  description = "FastAgent config YAML content. Update via gcloud secrets versions add."
  type        = string
  sensitive   = true
  default     = "# Placeholder - update secret manually"
}

variable "fastagent_secrets_yaml" {
  description = "FastAgent secrets YAML content (API keys). Update via gcloud secrets versions add."
  type        = string
  sensitive   = true
  default     = "# Placeholder - update secret manually"
}
