output "service_id" {
  description = "The ID of the Cloud Run service"
  value       = google_cloud_run_v2_service.cloudrun_service.id
}

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.cloudrun_service.name
}

output "service_uri" {
  description = "The URI of the Cloud Run service"
  value       = google_cloud_run_v2_service.cloudrun_service.uri
}

output "location" {
  description = "The location of the Cloud Run service"
  value       = google_cloud_run_v2_service.cloudrun_service.location
}
