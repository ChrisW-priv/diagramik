variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region for regional resources"
}

variable "network_name" {
  type        = string
  description = "Name of the VPC network"
}

variable "primary_subnet_cidr" {
  type        = string
  description = "CIDR range for the primary subnet (CloudRun Direct VPC egress)"
}
