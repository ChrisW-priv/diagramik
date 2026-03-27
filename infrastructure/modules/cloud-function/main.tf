resource "google_project_service" "services" {
  for_each           = toset(["cloudfunctions.googleapis.com", "cloudbuild.googleapis.com", "storage.googleapis.com"])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

# Shared GCS bucket for function source zips
resource "google_storage_bucket" "source" {
  name                        = "${var.google_project_id}-cf-source"
  project                     = var.google_project_id
  location                    = var.location
  force_destroy               = true
  uniform_bucket_level_access = true
  depends_on                  = [google_project_service.services]
}

# Sentinel zip — bootstraps infrastructure before real code is deployed
data "archive_file" "sentinel" {
  type        = "zip"
  output_path = "${path.module}/sentinel.zip"
  source {
    content  = "import functions_framework\n\n@functions_framework.http\ndef main(request):\n    return 'sentinel', 200\n"
    filename = "main.py"
  }
}

resource "google_storage_bucket_object" "sentinel" {
  name   = "sentinel/sentinel-${data.archive_file.sentinel.output_md5}.zip"
  bucket = google_storage_bucket.source.name
  source = data.archive_file.sentinel.output_path
}

# One service account per function
resource "google_service_account" "sa" {
  for_each     = var.functions
  project      = var.google_project_id
  account_id   = "${each.key}-sa"
  display_name = "Service account for Cloud Function ${each.key}"
}

# Grant any project-level IAM roles requested per function
resource "google_project_iam_member" "sa_roles" {
  for_each = {
    for pair in flatten([
      for fn_name, fn in var.functions : [
        for role in coalesce(fn.sa_iam_roles, []) : {
          key  = "${fn_name}-${role}"
          sa   = fn_name
          role = role
        }
      ]
    ]) : pair.key => pair
  }
  project = var.google_project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.sa[each.value.sa].email}"
}

# Cloud Functions v2 resources
resource "google_cloudfunctions2_function" "function" {
  for_each    = var.functions
  name        = each.key
  location    = var.location
  project     = var.google_project_id
  description = each.value.description
  depends_on  = [google_project_service.services]

  build_config {
    runtime     = coalesce(each.value.runtime, "python313")
    entry_point = coalesce(each.value.entry_point, "main")
    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.sentinel.name
      }
    }
  }

  service_config {
    available_memory      = coalesce(each.value.available_memory, "256M")
    available_cpu         = coalesce(each.value.available_cpu, "1")
    timeout_seconds       = coalesce(each.value.timeout_seconds, 60)
    min_instance_count    = coalesce(each.value.min_instance_count, 0)
    max_instance_count    = coalesce(each.value.max_instance_count, 100)
    ingress_settings      = coalesce(each.value.ingress_settings, "ALLOW_ALL")
    service_account_email = google_service_account.sa[each.key].email
    environment_variables = coalesce(each.value.environment_variables, {})

    dynamic "secret_environment_variables" {
      for_each = coalesce(each.value.secret_environment_variables, {})
      content {
        key        = secret_environment_variables.key
        project_id = var.google_project_id
        secret     = secret_environment_variables.value.secret
        version    = secret_environment_variables.value.version
      }
    }
  }

  dynamic "event_trigger" {
    for_each = each.value.event_trigger != null ? [each.value.event_trigger] : []
    content {
      event_type   = event_trigger.value.event_type
      retry_policy = coalesce(event_trigger.value.retry_policy, "RETRY_POLICY_RETRY")
      dynamic "event_filters" {
        for_each = coalesce(event_trigger.value.event_filters, [])
        content {
          attribute = event_filters.value.attribute
          value     = event_filters.value.value
        }
      }
    }
  }
}

# IAM invoker bindings per function
resource "google_cloudfunctions2_function_iam_member" "invoker" {
  for_each = {
    for pair in flatten([
      for fn_name, fn in var.functions : [
        for member in coalesce(fn.invoker_members, []) : {
          key    = "${fn_name}--${replace(member, ":", "-")}"
          fn     = fn_name
          member = member
        }
      ]
    ]) : pair.key => pair
  }
  project        = var.google_project_id
  location       = var.location
  cloud_function = google_cloudfunctions2_function.function[each.value.fn].name
  role           = "roles/cloudfunctions.invoker"
  member         = each.value.member
}
