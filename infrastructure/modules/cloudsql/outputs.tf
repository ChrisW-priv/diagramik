output "instance" {
  description = "The Cloud SQL instance for connecting applications."
  value       = google_sql_database_instance.instance.connection_name
}

output "connection_name" {
  description = "The connection name of the Cloud SQL instance for connecting applications."
  value       = google_sql_database_instance.instance.connection_name
}

output "instance_name" {
  value = google_sql_database_instance.instance.name
}

output "db_admin_user" {
  description = "The username for the PostgreSQL database admin user."
  value       = google_sql_user.admin_user.name
}

output "db_password_secret_id" {
  description = "The Secret Manager secret ID for the PostgreSQL database password."
  value       = module.db_password.secret_id
}

output "db_name" {
  description = "The name of the database."
  value       = var.database_name
}
