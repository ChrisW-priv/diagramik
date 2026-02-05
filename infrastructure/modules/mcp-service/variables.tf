# Required inputs
variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  type        = string
  description = "The location of the Cloud Run service."
}

variable "application_name" {
  type        = string
  description = "The name of the application."
}

variable "image_url" {
  type        = string
  description = "The MCP Docker image URL."
}

variable "diagrams_bucket_name" {
  type        = string
  description = "The name of the GCS bucket for diagrams."
}

# Environment extension inputs
variable "extra_env_vars" {
  description = "Additional environment variables to merge with base config."
  type        = map(string)
  default     = {}
}

variable "extra_secret_env_vars" {
  description = "Additional secret environment variables to merge with base config."
  type = map(object({
    secret_id      = string
    secret_version = optional(string)
  }))
  default = {}
}

variable "extra_volumes" {
  description = "Additional volumes to merge with base config."
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

variable "extra_volume_mounts" {
  description = "Additional volume mounts to merge with base config."
  type        = map(string)
  default     = {}
}

variable "extra_secret_access" {
  description = "List of secret IDs that the service account needs access to (for externally-provided secrets)."
  type        = set(string)
  default     = []
}

# Optional overrides
variable "memory_limit" {
  description = "The memory limit for the Cloud Run service."
  type        = string
  default     = "512Mi"
}

variable "cpu_limit" {
  description = "The CPU limit for the Cloud Run service."
  type        = string
  default     = "1"
}

variable "ingress" {
  description = "Ingress traffic sources."
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access."
  type        = bool
  default     = true
}

# VPC Networking Configuration
variable "vpc_network_self_link" {
  description = "VPC network self link for CloudRun Direct VPC egress (null to disable)"
  type        = string
  default     = null
}

variable "vpc_subnetwork_self_link" {
  description = "VPC subnetwork self link for CloudRun Direct VPC egress (null to disable)"
  type        = string
  default     = null
}

variable "vpc_egress" {
  description = "VPC egress setting: PRIVATE_RANGES_ONLY or ALL_TRAFFIC"
  type        = string
  default     = "PRIVATE_RANGES_ONLY"
}

# Service-to-service authentication
variable "django_service_account_email" {
  description = "Django service account email for IAM invoker binding (null to disable)"
  type        = string
  default     = null
}
