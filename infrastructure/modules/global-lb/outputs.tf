output "global_ip_address" {
  description = "The global static IP address"
  value       = google_compute_global_address.default.address
}

output "global_ip_name" {
  description = "The name of the global static IP"
  value       = google_compute_global_address.default.name
}

output "ssl_certificate_name" {
  description = "The name of the managed SSL certificate"
  value       = google_compute_managed_ssl_certificate.default.name
}

output "url_map_name" {
  description = "The name of the URL map"
  value       = google_compute_url_map.default.name
}

output "backend_bucket_name" {
  description = "The name of the backend bucket"
  value       = google_compute_backend_bucket.frontend.name
}

output "backend_service_name" {
  description = "The name of the API backend service (deprecated, use backend_services)"
  value       = try(google_compute_backend_service.cloudrun_backends["api"].name, "")
}

output "backend_services" {
  description = "Map of all backend service names"
  value = {
    for k, v in google_compute_backend_service.cloudrun_backends : k => v.name
  }
}

output "backend_negs" {
  description = "Map of all Network Endpoint Group IDs"
  value = {
    for k, v in google_compute_region_network_endpoint_group.cloudrun_neg : k => v.id
  }
}
