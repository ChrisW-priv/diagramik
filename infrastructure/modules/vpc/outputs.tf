output "network_id" {
  value       = google_compute_network.vpc.id
  description = "VPC network ID"
}

output "network_self_link" {
  value       = google_compute_network.vpc.self_link
  description = "VPC network self link (required for Cloud SQL and CloudRun)"
}

output "network_name" {
  value       = google_compute_network.vpc.name
  description = "VPC network name"
}

output "primary_subnet_id" {
  value       = google_compute_subnetwork.primary.id
  description = "Primary subnet ID"
}

output "primary_subnet_self_link" {
  value       = google_compute_subnetwork.primary.self_link
  description = "Primary subnet self link (required for CloudRun)"
}

output "primary_subnet_name" {
  value       = google_compute_subnetwork.primary.name
  description = "Primary subnet name"
}

output "private_vpc_connection_id" {
  value       = google_service_networking_connection.cloudsql_private_vpc_connection.id
  description = "Private VPC connection ID (for dependency management)"
}
