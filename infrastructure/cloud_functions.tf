locals {
  cloud_functions = {
    # "<function-name>" = {
    #   description = "<description>"
    #   environment_variables = {
    #     "MY_VAR" = "my-value"
    #   }
    #   invoker_members = ["allUsers"]
    # }
  }
}

module "cloud_functions" {
  source            = "./modules/cloud-function"
  google_project_id = var.google_project_id
  location          = var.google_region
  functions         = local.cloud_functions
}
