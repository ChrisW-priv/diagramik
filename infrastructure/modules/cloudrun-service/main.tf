resource "google_project_service" "service" {
  for_each = toset([
    "run.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_cloud_run_v2_service" "cloudrun_service" {
  name                = var.application_name
  project             = var.google_project_id
  location            = var.location
  deletion_protection = false
  ingress             = var.ingress
  depends_on          = [google_project_service.service]

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

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
      name  = "app"
      image = var.image_url

      resources {
        limits = {
          "memory" = var.memory_limit
          "cpu"    = var.cpu_limit
        }
        cpu_idle = true
      }

      ports {
        name           = var.port_name
        container_port = var.port_number
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

resource "google_cloud_run_v2_service_iam_member" "noauth" {
  count    = var.allow_unauthenticated ? 1 : 0
  project  = google_cloud_run_v2_service.cloudrun_service.project
  location = google_cloud_run_v2_service.cloudrun_service.location
  name     = google_cloud_run_v2_service.cloudrun_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
