variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  type        = string
  description = "The location of the storage bucket."
}

variable "name" {
  type        = string
  description = "The name of the Job."
}

variable "command" {
  type        = list(string)
  description = "The command to run in the container."
}

variable "args" {
  type        = list(string)
  description = "The arguments to pass to the command."
}

variable "service_account_email" {
  type        = string
  description = "The email of the service account."
}

variable "image_url" {
  type        = string
  description = "The URL of the Docker image."
}

variable "memory_limit" {
  type        = string
  description = "The memory limit for the job."
  default     = "1Gi"
}

variable "cpu_limit" {
  type        = string
  description = "The CPU limit for the job."
  default     = "1"
}


variable "max_retries" {
  type        = number
  description = "The maximum number of retries."
  default     = 0
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
