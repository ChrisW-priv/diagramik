variable "google_project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "location" {
  description = "The location of the storage bucket"
  type        = string
}

variable "application_name" {
  description = "The name of the application"
  type        = string
}

variable "index_page" {
  description = "The index page for the website"
  type        = string
  default     = "index.html"
}

variable "error_page" {
  description = "The error page for the website"
  type        = string
  default     = "404.html"
}
