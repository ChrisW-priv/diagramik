variable "google_project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location" {
  type        = string
  description = "The location of the storage bucket."
}

variable "secret_name" {
  type        = string
  description = "The name of the secret."
}

variable "secret_data" {
  type        = string
  description = "The data to be stored in the secret. If not provided, a random password will be generated."
  sensitive   = true
  default     = ""
}

variable "members" {
  type        = set(string)
  description = "List of members to grant access to the secret."
  default     = []
}

variable "length" {
  type        = number
  description = "Length of the randomly generated sequence"
  default     = 32
}

