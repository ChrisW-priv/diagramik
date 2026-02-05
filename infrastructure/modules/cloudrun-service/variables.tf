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

variable "service_account_email" {
  type        = string
  description = "The email of the service account."
}

variable "image_url" {
  type        = string
  description = "The URL of the Docker image."
}

variable "port_name" {
  type        = string
  description = "OPTIONAL: The name of the port (default: h2c)."
  default     = "h2c"
}

variable "port_number" {
  type        = number
  description = "OPTIONAL: The number of the port (default: 8080)."
  default     = 8080
}

variable "min_instance_count" {
  type        = number
  description = "The minimum number of instances to run."
  default     = 0
}

variable "max_instance_count" {
  type        = number
  description = "The maximum number of instances to run."
  default     = 1
}

variable "cpu_limit" {
  type        = string
  description = "The CPU limit for the Cloud Run service."
  default     = "1"
}

variable "memory_limit" {
  type        = string
  description = "The memory limit for the Cloud Run service."
  default     = "1Gi"
}

variable "volumes" {
  description = "Map of volume configurations"
  type = map(object({
    # GCS-specific (inferred if gcs_bucket is set)
    gcs_bucket   = optional(string)
    gcs_readonly = optional(bool, false)

    # Cloud SQL-specific (inferred if cloudsql_instances is set)
    cloudsql_instances = optional(list(string))

    # Secret-specific (inferred if secret_name is set)
    secret_name = optional(string)
    secret_items = optional(list(object({
      version = string
      path    = string
      mode    = optional(number, 0444)
    })))

    # EmptyDir-specific (inferred if emptydir_medium or size_limit is set)
    emptydir_medium     = optional(string)
    emptydir_size_limit = optional(string)
  }))
  default = {}
}

variable "volume_mounts" {
  description = "Map of volume mount configurations"
  type        = map(string)
  default     = {}
}

variable "env_vars" {
  description = "Map of environment variables"
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Map of secret environment variables"
  type = map(object({
    secret_id      = string
    secret_version = optional(string)
  }))
  default = {}
}

variable "ingress" {
  description = "Ingress traffic sources. INGRESS_TRAFFIC_ALL, INGRESS_TRAFFIC_INTERNAL_ONLY, or INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  type        = string
  default     = "INGRESS_TRAFFIC_INTERNAL_ONLY"
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access (allUsers gets roles/run.invoker)"
  type        = bool
  default     = false
}

# VPC Networking Configuration for Direct VPC Egress
variable "vpc_network_self_link" {
  description = "VPC network self link for Direct VPC egress (null to disable)"
  type        = string
  default     = null
}

variable "vpc_subnetwork_self_link" {
  description = "VPC subnetwork self link for Direct VPC egress (null to disable)"
  type        = string
  default     = null
}

variable "vpc_egress" {
  description = "VPC egress setting: PRIVATE_RANGES_ONLY (default) or ALL_TRAFFIC"
  type        = string
  default     = "PRIVATE_RANGES_ONLY"
}

