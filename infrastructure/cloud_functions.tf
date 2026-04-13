locals {
  cloud_functions = {
    "share-diagram-image" = {
      description     = "Resolves share tokens and redirects to diagram images"
      invoker_members = ["allUsers"]
      environment_variables = {
        "DB_PRIVATE_IP"          = module.diagramik.db_private_ip
        "POSTGRES_USER"          = module.diagramik.db_user
        "POSTGRES_DATABASE_NAME" = module.diagramik.db_name
      }
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
