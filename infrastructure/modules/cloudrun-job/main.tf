resource "google_project_service" "service" {
  for_each = toset([
    "run.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_cloud_run_v2_job" "backend_setup_job" {
  name                = var.name
  project             = var.google_project_id
  location            = var.location
  deletion_protection = false
  depends_on          = [google_project_service.service]

  template {
    template {
      service_account = var.service_account_email
      max_retries     = var.max_retries

      dynamic "volumes" {
        for_each = var.volumes
        content {
          name = volumes.key

          # GCS volume
          dynamic "gcs" {
            for_each = volumes.value.gcs_bucket != null ? [1] : []
            content {
              bucket    = volumes.value.gcs_bucket
              read_only = volumes.value.gcs_readonly
            }
          }

          # Cloud SQL volume
          dynamic "cloud_sql_instance" {
            for_each = volumes.value.cloudsql_instances != null ? [1] : []
            content {
              instances = volumes.value.cloudsql_instances
            }
          }

          # Secret volume
          dynamic "secret" {
            for_each = volumes.value.secret_name != null ? [1] : []
            content {
              secret       = volumes.value.secret_name
              default_mode = 0444

              dynamic "items" {
                for_each = volumes.value.secret_items != null ? volumes.value.secret_items : []
                content {
                  version = items.value.version
                  path    = items.value.path
                  mode    = items.value.mode
                }
              }
            }
          }

          # EmptyDir volume
          dynamic "empty_dir" {
            for_each = volumes.value.emptydir_medium != null ? [1] : []
            content {
              medium     = volumes.value.emptydir_medium
              size_limit = volumes.value.emptydir_size_limit
            }
          }
        }
      }

      containers {
        image   = var.image_url
        command = var.command
        args    = var.args

        resources {
          limits = {
            "memory" = var.memory_limit
            "cpu"    = var.cpu_limit
          }
        }

        dynamic "volume_mounts" {
          for_each = var.volume_mounts
          content {
            name       = volume_mounts.key
            mount_path = volume_mounts.value
          }
        }

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = var.secret_env_vars
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = env.value.secret_id
                version = env.value.secret_version != null ? env.value.secret_version : "latest"
              }
            }
          }
        }
      }
    }
  }
}
