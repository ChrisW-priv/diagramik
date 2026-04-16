locals {
  cloud_functions = {
    "render-diagram" = {
      description      = "Renders Mermaid and architecture diagrams and uploads to GCS"
      invoker_members  = []
      available_memory = "1Gi"
      available_cpu    = "2"
      timeout_seconds  = 120
      environment_variables = {
        "GCP_PROJECT_ID" = var.google_project_id
        "BUCKET_NAME"    = module.diagramik.diagrams_bucket_name
      }
    }
    "share-diagram-image" = {
      description     = "Resolves share tokens and redirects to diagram images"
      invoker_members = ["allUsers"]
      environment_variables = {
        "DB_PRIVATE_IP"              = module.diagramik.db_private_ip
        "POSTGRES_USER"              = module.diagramik.db_user
        "POSTGRES_DATABASE_NAME"     = module.diagramik.db_name
        "SIGNED_URL_SA_KEY_FILENAME" = "/secrets/gcs/key.json"
      }
      secret_volumes = [
        {
          mount_path = "/secrets/gcs"
          secret     = module.gcs-sa-key-secret.secret_id
          version    = "latest"
          path       = "key.json"
        }
      ]
      secret_environment_variables = {
        "POSTGRES_PASSWORD" = {
          secret  = module.diagramik.db_password_secret_id
          version = "latest"
        }
      }
    }
  }
}

module "cloud_functions" {
  source              = "./modules/cloud-function"
  google_project_id   = var.google_project_id
  location            = var.google_region
  functions           = local.cloud_functions
  vpc_network_name    = module.vpc.network_name
  vpc_subnetwork_name = module.vpc.primary_subnet_name
}

# Grant the function's SA access to read the DB password secret
resource "google_secret_manager_secret_iam_member" "cf_db_password" {
  secret_id = module.diagramik.db_password_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.cloud_functions.service_account_emails["share-diagram-image"]}"
}

# Grant the function's SA access to read the GCS SA key secret
resource "google_secret_manager_secret_iam_member" "cf_gcs_sa_key" {
  secret_id = module.gcs-sa-key-secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.cloud_functions.service_account_emails["share-diagram-image"]}"
}

# Grant render-diagram SA objectUser access to the diagrams bucket
resource "google_storage_bucket_iam_member" "render_diagram_gcs" {
  bucket = module.diagramik.diagrams_bucket_name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${module.cloud_functions.service_account_emails["render-diagram"]}"
}
