resource "google_service_account" "sa" {
  project      = var.google_project_id
  account_id   = "${var.application_name}-sa"
  display_name = "${var.application_name} Service Account"
}

# Artifact Registry for Docker images
module "artifact-registry" {
  source            = "../artifact-registry"
  google_project_id = var.google_project_id
  location          = var.location
  repository_id     = var.application_name
  description       = "${var.application_name} docker images"
  readers           = [google_service_account.sa.member]
  writers = var.github_repository != "" && var.workload_identity_pool_id != "" ? [
    "principalSet://iam.googleapis.com/${var.workload_identity_pool_id}/attribute.repository/${var.github_repository}"
  ] : []
}

locals {
  backend_monolith_image_url  = "${module.artifact-registry.repository_url}/application-monolith:${var.docker_image_tag}"
  backend_setup_job_image_url = "${module.artifact-registry.repository_url}/application-monolith:${var.docker_image_tag}"
  mcp_image_url               = "${module.artifact-registry.repository_url}/diagramming-mcp:${var.docker_image_tag}"

  # Base Django configuration
  django_base_volumes = {
    "cloudsql" = {
      cloudsql_instances = [module.postgres_db.connection_name]
    }
  }

  django_base_volume_mounts = {
    "cloudsql" = "/cloudsql"
  }

  django_base_env_vars = {
    "LOGGING_LEVEL"          = "INFO"
    "GCP_PROJECT_ID"         = var.google_project_id
    "DIAGRAMS_BUCKET_NAME"   = module.diagrams-bucket.name
    "STATIC_BUCKET_NAME"     = module.public-bucket.name
    "MEDIA_BUCKET_NAME"      = module.private-bucket.name
    "DB_CONN_NAME"           = module.postgres_db.connection_name
    "POSTGRES_DATABASE_NAME" = module.postgres_db.db_name
    "POSTGRES_USER"          = module.postgres_db.db_admin_user
    "DEPLOYMENT_ENVIRONMENT" = "PRODUCTION_SERVICE"
  }

  django_base_secret_env_vars = {
    "POSTGRES_PASSWORD" = {
      secret_id = module.postgres_db.db_password_secret_id
    }
    "DEFAULT_SECRET_KEY" = {
      secret_id = module.django-monolith-secret-key.secret_id
    }
  }

  # Merge base with extra (extra takes precedence)
  django_merged_volumes         = merge(local.django_base_volumes, var.extra_django_volumes)
  django_merged_volume_mounts   = merge(local.django_base_volume_mounts, var.extra_django_volume_mounts)
  django_merged_env_vars        = merge(local.django_base_env_vars, var.extra_django_env_vars)
  django_merged_secret_env_vars = merge(local.django_base_secret_env_vars, var.extra_django_secret_env_vars)
}

# Storage buckets
module "diagrams-bucket" {
  source            = "../storage-bucket"
  name              = "${var.application_name}-diagrams"
  google_project_id = var.google_project_id
  location          = var.location
  permissions = [
    {
      member = google_service_account.sa.member
      role   = "roles/storage.objectUser"
    }
  ]
}

module "public-bucket" {
  source            = "../storage-bucket"
  name              = "${var.application_name}-public"
  google_project_id = var.google_project_id
  location          = var.location
  permissions = [
    {
      member = "allUsers"
      role   = "roles/storage.objectViewer"
    },
    {
      member = google_service_account.sa.member
      role   = "roles/storage.objectUser"
    }
  ]
}

module "private-bucket" {
  source            = "../storage-bucket"
  name              = "${var.application_name}-private"
  google_project_id = var.google_project_id
  location          = var.location
  permissions = [
    {
      member = google_service_account.sa.member
      role   = "roles/storage.objectUser"
    }
  ]
}

# Secrets
module "django-monolith-secret-key" {
  source            = "../secret"
  google_project_id = var.google_project_id
  location          = var.location
  secret_name       = "${upper(var.application_name)}_DJANGO_SECRET_KEY"
  members           = [google_service_account.sa.member]
  length            = 64
}

module "django-monolith-admin-password" {
  source            = "../secret"
  google_project_id = var.google_project_id
  location          = var.location
  secret_name       = "${upper(var.application_name)}_DJANGO_ADMIN_PASSWORD"
  members           = [google_service_account.sa.member]
}

# Database
module "postgres_db" {
  source            = "../cloudsql"
  google_project_id = var.google_project_id
  google_region     = var.location
  instance_name     = "django-monolith-postgres"
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.google_project_id
  role    = "roles/cloudsql.client"
  member  = google_service_account.sa.member
}

resource "google_secret_manager_secret_iam_member" "db_password_access" {
  secret_id = module.postgres_db.db_password_secret_id
  member    = google_service_account.sa.member
  role      = "roles/secretmanager.secretAccessor"
}

# Setup Job
module "monolith-setup-job" {
  source                = "../cloudrun-job"
  google_project_id     = var.google_project_id
  name                  = "${var.application_name}-setup-job"
  location              = var.location
  image_url             = local.backend_setup_job_image_url
  service_account_email = google_service_account.sa.email
  max_retries           = 0
  command               = ["/app/django_monolith/entrypoint.sh"]
  args                  = ["setup"]

  volumes = {
    "cloudsql" = {
      cloudsql_instances = [module.postgres_db.connection_name]
    }
  }

  volume_mounts = {
    "cloudsql" = "/cloudsql"
  }

  env_vars = {
    "DB_CONN_NAME"           = module.postgres_db.connection_name
    "POSTGRES_DATABASE_NAME" = module.postgres_db.db_name
    "POSTGRES_USER"          = module.postgres_db.db_admin_user
    "STATIC_BUCKET_NAME"     = module.public-bucket.name
    "MEDIA_BUCKET_NAME"      = module.private-bucket.name
  }

  secret_env_vars = {
    "POSTGRES_PASSWORD" = {
      secret_id = module.postgres_db.db_password_secret_id
    }
    "DJANGO_SUPERUSER_PASSWORD" = {
      secret_id = module.django-monolith-admin-password.secret_id
    }
  }
  depends_on = [module.django-monolith-admin-password, module.postgres_db]
}

# Django Monolith Cloud Run Service
module "django-monolith" {
  source                = "../cloudrun-service"
  google_project_id     = var.google_project_id
  application_name      = var.application_name
  location              = var.location
  image_url             = local.backend_monolith_image_url
  service_account_email = google_service_account.sa.email
  ingress               = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  allow_unauthenticated = true
  volumes               = local.django_merged_volumes
  volume_mounts         = local.django_merged_volume_mounts
  env_vars              = local.django_merged_env_vars
  secret_env_vars       = local.django_merged_secret_env_vars

  depends_on = [
    module.django-monolith-secret-key,
    google_secret_manager_secret_iam_member.extra_secret_access
  ]
}

# Dependency anchor - ensures external secrets exist before IAM bindings
# This creates a proper dependency chain when used with module-level depends_on
resource "terraform_data" "extra_secrets_ready" {
  for_each = var.extra_secret_access
  input    = each.value
}

# Grant access to externally-provided secrets
resource "google_secret_manager_secret_iam_member" "extra_secret_access" {
  for_each  = var.extra_secret_access
  secret_id = each.value
  member    = google_service_account.sa.member
  role      = "roles/secretmanager.secretAccessor"

  depends_on = [terraform_data.extra_secrets_ready]
}

