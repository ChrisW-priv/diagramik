variable "google_project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "location" {
  description = "The GCP region/location for Cloud Functions"
  type        = string
}

variable "vpc_network_name" {
  description = "VPC network name for direct VPC egress"
  type        = string
}

variable "vpc_subnetwork_name" {
  description = "VPC subnetwork name for direct VPC egress"
  type        = string
}

variable "functions" {
  description = "Map of Cloud Function configurations"
  type = map(object({
    description           = string
    runtime               = optional(string, "python313")
    entry_point           = optional(string, "main")
    available_memory      = optional(string, "256M")
    available_cpu         = optional(string, "1")
    timeout_seconds       = optional(number, 60)
    min_instance_count    = optional(number, 0)
    max_instance_count    = optional(number, 100)
    ingress_settings      = optional(string, "ALLOW_ALL")
    environment_variables = optional(map(string), {})
    secret_environment_variables = optional(map(object({
      secret  = string
      version = string
    })), {})
    sa_iam_roles    = optional(list(string), [])
    invoker_members = optional(list(string), [])
    event_trigger = optional(object({
      event_type   = string
      retry_policy = optional(string, "RETRY_POLICY_RETRY")
      event_filters = optional(list(object({
        attribute = string
        value     = string
      })), [])
    }), null)
  }))
  default = {}
}
