locals {
  cloud_functions = {
    "share-diagram-image" = {
      description     = "Resolves share tokens and redirects to diagram images"
      invoker_members = []
      environment_variables = {
        "MONOLITH_URL" = "https://${var.domain}"
      }
      secret_environment_variables = {}
    }
  }
}

module "cloud_functions" {
  source            = "./modules/cloud-function"
  google_project_id = var.google_project_id
  location          = var.google_region
  functions         = local.cloud_functions
}
