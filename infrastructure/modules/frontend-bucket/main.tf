resource "google_project_service" "storage" {
  project            = var.google_project_id
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_storage_bucket" "frontend" {
  name                        = "${var.application_name}-frontend"
  project                     = var.google_project_id
  location                    = var.location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  website {
    main_page_suffix = var.index_page
    not_found_page   = var.error_page
  }

  depends_on = [google_project_service.storage]
}

resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
