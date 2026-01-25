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
  description = "The name of the storage bucket."
}

variable "storage_class" {
  type        = string
  description = "The storage class of the storage bucket."
  default     = "STANDARD"
}

variable "force_destroy" {
  type        = bool
  description = "Whether to force the destruction of the storage bucket."
  default     = false
}

variable "uniform_bucket_level_access" {
  type        = bool
  description = "Whether to enable uniform bucket-level access for the storage bucket."
  default     = true
}

variable "permissions" {
  description = "List of member-role permissions for the storage bucket."
}
