resource "google_project_service" "service" {
  for_each = toset([
    "secretmanager.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_secret_manager_secret" "secret" {
  project    = var.google_project_id
  secret_id  = var.secret_name
  depends_on = [google_project_service.service]
  replication {
    user_managed {
      replicas {
        location = var.location
      }
    }
  }
}

resource "random_password" "secret" {
  length  = 32
  special = false
}

locals {
  secret_data = var.secret_data == "" ? random_password.secret.result : var.secret_data
}

resource "google_secret_manager_secret_version" "secret_version" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = local.secret_data
  depends_on  = [google_secret_manager_secret.secret]
}

resource "google_secret_manager_secret_iam_member" "access" {
  for_each  = var.members
  project   = var.google_project_id
  secret_id = google_secret_manager_secret.secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value
}
