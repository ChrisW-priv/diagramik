resource "google_project_service" "service" {
  for_each = toset([
    "sqladmin.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_sql_database_instance" "instance" {
  database_version = var.database_version
  name             = var.instance_name
  project          = var.google_project_id
  region           = var.google_region
  depends_on       = [google_project_service.service]
  settings {
    tier = var.instance_tier
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
