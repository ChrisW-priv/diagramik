variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  type        = string
  description = "The location of the artifact registry."
}

variable "repository_id" {
  type        = string
  description = "The repository ID."
}

variable "description" {
  type        = string
  description = "Description of the repository."
  default     = "Docker container images"
}

variable "keep_count" {
  type        = number
  description = "Number of recent versions to keep per image."
  default     = 10
}

variable "readers" {
  type        = list(string)
  description = "List of IAM members that can read from this repository."
  default     = []
}

variable "writers" {
  type        = list(string)
  description = "List of IAM members that can write to this repository."
  default     = []
}
