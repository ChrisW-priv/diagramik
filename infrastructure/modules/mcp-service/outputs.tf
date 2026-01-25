output "service_id" {
  description = "The ID of the MCP Cloud Run service"
  value       = module.mcp-service.service_id
}

output "service_name" {
  description = "The name of the MCP Cloud Run service"
  value       = module.mcp-service.service_name
}

output "service_uri" {
  description = "The URI of the MCP Cloud Run service"
  value       = module.mcp-service.service_uri
}

output "location" {
  description = "The location of the MCP Cloud Run service"
  value       = module.mcp-service.location
}

output "service_account_email" {
  description = "The service account email for the MCP service"
  value       = google_service_account.mcp_sa.email
}

output "service_account_member" {
  description = "The service account member string for IAM"
  value       = google_service_account.mcp_sa.member
}
