output "secret_id" {
  value       = google_secret_manager_secret.secret.secret_id
  description = "The ID of the secret"
}

output "secret_value" {
  value     = var.secret_data != "" ? var.secret_data : random_password.secret.result
  sensitive = true
}
