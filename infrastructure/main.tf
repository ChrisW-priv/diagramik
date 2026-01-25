module "vertex-ai-secret" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "VERTEX_AI_API_SECRET_KEY"
  secret_data       = var.gcs_sa_key_json
}

module "gcs-sa-key-secret" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "${upper(replace(var.application_name, "-", "_"))}_GCS_SA_KEY"
}

module "email-labs-api-app-key" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "EMAIL_LABS_API_APP_KEY"
}

module "email-labs-api-secret-key" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "EMAIL_LABS_API_SECRET_KEY"
}

module "oauth-client-id" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "GOOGLE_OAUTH_CLIENT_ID"
}

module "oauth-client-secret" {
  source            = "./modules/secret"
  google_project_id = var.google_project_id
  location          = var.google_region
  secret_name       = "GOOGLE_OAUTH_CLIENT_SECRET"
}

resource "google_service_account" "sa" {
  project      = var.google_project_id
  account_id   = "gcs-signed-url-generation-sa"
  display_name = "Used to generate Signed URLs"
}

resource "google_storage_bucket_iam_member" "bucket_A" {
  bucket = "diagramik-diagrams"
  role   = "roles/storage.legacyObjectReader"
  member = google_service_account.sa.member
}

# Django Monolith (includes Cloud Run services, buckets, secrets, DB)
module "diagramik" {
  source                    = "./modules/django-monolith"
  google_project_id         = var.google_project_id
  location                  = var.google_region
  application_name          = var.application_name
  docker_image_tag          = var.docker_image_tag
  github_repository         = var.github_repository
  workload_identity_pool_id = var.workload_identity_pool_id
  depends_on = [
    module.gcs-sa-key-secret,
  ]

  # Pass secrets as extra volumes
  extra_django_volumes = {
    "gcs-sa-key" = {
      secret_name = module.gcs-sa-key-secret.secret_id
      secret_items = [
        {
          version = "latest"
          path    = "key.json"
        }
      ]
    }
  }

  extra_django_volume_mounts = {
    "gcs-sa-key" = "/secrets/gcs"
  }

  extra_django_env_vars = {
    "SIGNED_URL_SA_KEY_FILENAME" = "/secrets/gcs/key.json"
  }

  extra_django_secret_env_vars = {
    "EMAILLABS_API_APP_KEY" = {
      secret_id = module.email-labs-api-app-key.secret_id
    }
    "EMAILLABS_API_SECRET_KEY" = {
      secret_id = module.email-labs-api-secret-key.secret_id
    }
    "GOOGLE_OAUTH_CLIENT_ID" = {
      secret_id = module.oauth-client-id.secret_id
    }
    "GOOGLE_OAUTH_CLIENT_SECRET" = {
      secret_id = module.oauth-client-secret.secret_id
    }
    "GOOGLE_API_KEY" = {
      secret_id = module.vertex-ai-secret.secret_id
    }
  }
  extra_secret_access = [
    module.gcs-sa-key-secret.secret_id,
    module.vertex-ai-secret.secret_id,
    module.oauth-client-id.secret_id,
    module.oauth-client-secret.secret_id,
    module.email-labs-api-app-key.secret_id,
    module.email-labs-api-secret-key.secret_id,
  ]
}

# MCP Service (diagram generation)
module "mcp-service" {
  source = "./modules/mcp-service"

  google_project_id    = var.google_project_id
  location             = var.google_region
  application_name     = var.application_name
  image_url            = module.diagramik.mcp_image_url
  diagrams_bucket_name = module.diagramik.diagrams_bucket_name
  ingress              = "INGRESS_TRAFFIC_ALL"
}

# Frontend Bucket for static files
module "frontend-bucket" {
  source            = "./modules/frontend-bucket"
  google_project_id = var.google_project_id
  location          = var.google_region
  application_name  = var.application_name
}

# Global Load Balancer with path-based routing to multiple backends
module "global-lb" {
  source = "./modules/global-lb"

  google_project_id    = var.google_project_id
  application_name     = var.application_name
  domain               = var.domain
  additional_domains   = var.additional_domains
  frontend_bucket_name = module.frontend-bucket.bucket_name
  enable_cdn           = true

  # Configure multiple CloudRun backends with path-based routing
  cloudrun_backends = {
    # Django API backend - handles /api/* paths
    api = {
      service_name = module.diagramik.django_service_name
      location     = module.diagramik.django_service_location
      path_prefix  = "/api/*"
      priority     = 1 # Higher priority to match first
    }

    # MCP Diagram Service - ONLY accessible via /mcp/* path
    mcp = {
      service_name = module.mcp-service.service_name
      location     = module.mcp-service.location
      path_prefix  = "/mcp/*"
      priority     = 2
    }
  }
}
