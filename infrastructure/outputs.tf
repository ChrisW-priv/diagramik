output "global_ip_address" {
  description = "The global static IP address for DNS configuration"
  value       = module.global-lb.global_ip_address
}

output "django_service_uri" {
  description = "The URI of the Django Cloud Run service"
  value       = module.diagramik.django_service_uri
}

output "mcp_service_uri" {
  description = "The URI of the MCP Cloud Run service"
  value       = module.mcp-service.service_uri
}

output "artifact_registry_url" {
  description = "The URL of the artifact registry"
  value       = module.diagramik.artifact_registry_url
}

output "frontend_bucket_name" {
  description = "The name of the frontend bucket"
  value       = module.frontend-bucket.bucket_name
}

output "diagrams_bucket_name" {
  description = "The name of the diagrams bucket"
  value       = module.diagramik.diagrams_bucket_name
}
