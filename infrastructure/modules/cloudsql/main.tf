resource "google_project_service" "service" {
  for_each = toset([
    "sqladmin.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_sql_database_instance" "instance" {
  database_version    = var.database_version
  name                = var.instance_name
  project             = var.google_project_id
  region              = var.google_region
  deletion_protection = true

  # CRITICAL: Must wait for VPC peering connection before enabling private IP
  # Note: Terraform will ignore null dependencies automatically
  depends_on = [
    google_project_service.service
  ]

  settings {
    tier = var.instance_tier

    # IP Configuration for dual-mode (public + private) or single-mode
    ip_configuration {
      ipv4_enabled                                  = var.enable_public_ip
      private_network                               = var.enable_private_ip ? var.network_self_link : null
      enable_private_path_for_google_cloud_services = var.enable_private_ip
    }
  }
}

module "db_password" {
  source            = "../secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "DJANGO_MONOLITH_POSTGRES_DB_PASSWORD"
}

resource "google_sql_user" "admin_user" {
  name     = var.db_user
  instance = google_sql_database_instance.instance.name
  project  = var.google_project_id
  password = module.db_password.secret_value
}
