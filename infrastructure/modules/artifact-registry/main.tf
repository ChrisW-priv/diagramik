resource "google_project_service" "artifactregistry" {
  project            = var.google_project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  project       = var.google_project_id
  location      = var.location
  repository_id = var.repository_id
  description   = var.description
  format        = "DOCKER"

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"
    most_recent_versions {
      keep_count = var.keep_count
    }
  }

  depends_on = [google_project_service.artifactregistry]
}

resource "google_artifact_registry_repository_iam_member" "readers" {
  for_each   = { for idx, member in var.readers : idx => member }
  project    = var.google_project_id
  location   = var.location
  repository = google_artifact_registry_repository.repo.name
  role       = "roles/artifactregistry.reader"
  member     = each.value
}

resource "google_artifact_registry_repository_iam_member" "writers" {
  for_each   = { for idx, member in var.writers : idx => member }
  project    = var.google_project_id
  location   = var.location
  repository = google_artifact_registry_repository.repo.name
  role       = "roles/artifactregistry.writer"
  member     = each.value
}
