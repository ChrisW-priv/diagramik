resource "google_storage_bucket" "cloudbuild_staging" {
  name                        = "${var.google_project_id}-cloudbuild-staging"
  project                     = var.google_project_id
  location                    = var.google_region
  uniform_bucket_level_access = true
  force_destroy               = true

  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 1 }
  }
}
