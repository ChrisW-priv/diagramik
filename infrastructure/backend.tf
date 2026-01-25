terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }

  backend "gcs" {
    bucket = "tf-state-playground-449613"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.google_project_id
  region  = var.google_region
}

