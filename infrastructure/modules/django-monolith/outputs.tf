output "service_account_email" {
  description = "The service account email"
  value       = google_service_account.sa.email
}

output "service_account_member" {
  description = "The service account member string for IAM"
  value       = google_service_account.sa.member
}

output "django_service_name" {
  description = "The name of the Django Cloud Run service"
  value       = module.django-monolith.service_name
}

output "django_service_uri" {
  description = "The URI of the Django Cloud Run service"
  value       = module.django-monolith.service_uri
}

output "django_service_location" {
  description = "The location of the Django Cloud Run service"
  value       = module.django-monolith.location
}

output "artifact_registry_url" {
  description = "The URL of the artifact registry"
  value       = module.artifact-registry.repository_url
}

output "diagrams_bucket_name" {
  description = "The name of the diagrams bucket"
  value       = module.diagrams-bucket.name
}

output "mcp_image_url" {
  description = "The MCP Docker image URL"
  value       = local.mcp_image_url
}
