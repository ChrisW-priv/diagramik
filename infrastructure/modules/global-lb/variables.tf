variable "google_project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "application_name" {
  description = "The name of the application (used for resource naming)"
  type        = string
}

variable "domain" {
  description = "Primary domain for the application"
  type        = string
}

variable "additional_domains" {
  description = "Additional domains for SSL certificate"
  type        = list(string)
  default     = []
}

variable "frontend_bucket_name" {
  description = "Name of the GCS bucket for frontend static files"
  type        = string
}

variable "cloudrun_service_name" {
  description = "Name of the Cloud Run service for API backend (deprecated, use cloudrun_backends)"
  type        = string
  default     = ""
}

variable "cloudrun_service_location" {
  description = "Location/region of the Cloud Run service (deprecated, use cloudrun_backends)"
  type        = string
  default     = ""
}

variable "cloudrun_backends" {
  description = "Map of CloudRun backend services with path-based routing configuration"
  type = map(object({
    service_name = string
    location     = string
    path_prefix  = string # e.g., "/api/*" or "/mcp/*"
    priority     = number # Lower number = higher priority for path matching
  }))
  default = {}
}

variable "enable_cdn" {
  description = "Enable Cloud CDN for the frontend bucket"
  type        = bool
  default     = true
}

variable "api_path_prefix" {
  description = "Path prefix for API routing (deprecated, use cloudrun_backends)"
  type        = string
  default     = "/api/*"
}
