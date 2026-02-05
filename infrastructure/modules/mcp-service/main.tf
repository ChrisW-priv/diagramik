# Dedicated service account for MCP service
resource "google_service_account" "mcp_sa" {
  project      = var.google_project_id
  account_id   = "${var.application_name}-mcp-sa"
  display_name = "${var.application_name} MCP Service Account"
}

# Grant MCP SA access to the diagrams bucket
resource "google_storage_bucket_iam_member" "mcp_bucket_access" {
  bucket = var.diagrams_bucket_name
  member = google_service_account.mcp_sa.member
  role   = "roles/storage.objectUser"
}

# Grant access to externally-provided secrets
resource "google_secret_manager_secret_iam_member" "extra_secret_access" {
  for_each  = var.extra_secret_access
  secret_id = each.value
  member    = google_service_account.mcp_sa.member
  role      = "roles/secretmanager.secretAccessor"
}

locals {
  # Base MCP configuration
  base_env_vars = {
    "GCP_PROJECT_ID" = var.google_project_id
    "BUCKET_NAME"    = var.diagrams_bucket_name
  }

  # Merge base with extra (extra takes precedence)
  merged_volumes         = var.extra_volumes
  merged_volume_mounts   = var.extra_volume_mounts
  merged_env_vars        = merge(local.base_env_vars, var.extra_env_vars)
  merged_secret_env_vars = var.extra_secret_env_vars
}

module "mcp-service" {
  source                = "../cloudrun-service"
  google_project_id     = var.google_project_id
  application_name      = "${var.application_name}-mcp"
  location              = var.location
  image_url             = var.image_url
  port_name             = "http1"
  service_account_email = google_service_account.mcp_sa.email
  memory_limit          = var.memory_limit
  cpu_limit             = var.cpu_limit
  ingress               = var.ingress
  allow_unauthenticated = var.allow_unauthenticated
  volumes               = local.merged_volumes
  volume_mounts         = local.merged_volume_mounts
  env_vars              = local.merged_env_vars
  secret_env_vars       = local.merged_secret_env_vars

  # VPC Direct Egress configuration
  vpc_network_self_link    = var.vpc_network_self_link
  vpc_subnetwork_self_link = var.vpc_subnetwork_self_link
  vpc_egress               = var.vpc_egress

  depends_on = [
    google_secret_manager_secret_iam_member.extra_secret_access
  ]
}

# Grant Django service account permission to invoke MCP service
resource "google_cloud_run_v2_service_iam_member" "django_invoker" {
  count    = var.django_service_account_email != null ? 1 : 0
  project  = var.google_project_id
  location = module.mcp-service.location
  name     = module.mcp-service.service_name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.django_service_account_email}"
}
