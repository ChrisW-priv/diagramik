variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "google_region" {
  description = "The GCP region for the Cloud SQL instance."
  type        = string
}

variable "instance_name" {
  description = "The name of the Cloud SQL instance."
  type        = string
}

variable "instance_tier" {
  description = "(Optional) The machine type for the Cloud SQL instance (default: db-f1-micro)."
  type        = string
  default     = "db-f1-micro"
}

variable "db_user" {
  description = "(Optional) The username for the PostgreSQL database admin user (default: postgres)."
  type        = string
  default     = "postgres"
}

variable "database_name" {
  description = "(Optional) The name of the database to create within the instance (default: postgres)."
  type        = string
  default     = "postgres"
}

variable "database_version" {
  description = "The version of PostgreSQL to use."
  type        = string
  default     = "POSTGRES_15"
}

# VPC Networking Configuration
variable "network_self_link" {
  description = "VPC network self link for private IP (null to disable private IP)"
  type        = string
  default     = null
}

variable "enable_private_ip" {
  description = "Enable private IP for Cloud SQL"
  type        = bool
  default     = false
}

variable "enable_public_ip" {
  description = "Enable public IP for Cloud SQL (default true for backward compatibility)"
  type        = bool
  default     = false
}
