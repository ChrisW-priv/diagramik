output "repository_id" {
  description = "The repository ID"
  value       = google_artifact_registry_repository.repo.repository_id
}

output "repository_url" {
  description = "The URL of the repository (for docker push/pull)"
  value       = "${var.location}-docker.pkg.dev/${var.google_project_id}/${google_artifact_registry_repository.repo.repository_id}"
}

output "name" {
  description = "The full name of the repository"
  value       = google_artifact_registry_repository.repo.name
}
