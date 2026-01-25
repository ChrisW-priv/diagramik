variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  type        = string
  description = "The location of the storage bucket."
}

variable "application_name" {
  type        = string
  description = "The name of the application."
}

variable "docker_image_tag" {
  type        = string
  description = "The Docker image tag (commit SHA or 'latest')."
  default     = "latest"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in 'owner/repo' format for Workload Identity Federation."
  default     = ""
}

variable "workload_identity_pool_id" {
  type        = string
  description = "The ID of the Workload Identity Pool (e.g., 'projects/123/locations/global/workloadIdentityPools/github')."
  default     = ""
}

variable "extra_django_env_vars" {
  description = "Additional environment variables to merge with base Django config."
  type        = map(string)
  default     = {}
}

variable "extra_django_secret_env_vars" {
  description = "Additional secret environment variables to merge with base Django config."
  type = map(object({
    secret_id      = string
    secret_version = optional(string)
  }))
  default = {}
}

variable "extra_django_volumes" {
  description = "Additional volumes to merge with base Django config."
  type = map(object({
    gcs_bucket         = optional(string)
    gcs_readonly       = optional(bool, false)
    cloudsql_instances = optional(list(string))
    secret_name        = optional(string)
    secret_items = optional(list(object({
      version = string
      path    = string
      mode    = optional(number, 0444)
    })))
    emptydir_medium     = optional(string)
    emptydir_size_limit = optional(string)
  }))
  default = {}
}

variable "extra_django_volume_mounts" {
  description = "Additional volume mounts to merge with base Django config."
  type        = map(string)
  default     = {}
}

variable "extra_secret_access" {
  description = "List of secret IDs that the service account needs access to (for externally-provided secrets)."
  type        = set(string)
  default     = []
}
