resource "google_project_service" "service" {
  for_each = toset([
    "storage.googleapis.com",
  ])
  project            = var.google_project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_storage_bucket" "bucket" {
  name                        = var.name
  project                     = var.google_project_id
  location                    = var.location
  storage_class               = var.storage_class
  force_destroy               = var.force_destroy
  uniform_bucket_level_access = var.uniform_bucket_level_access
  depends_on                  = [google_project_service.service]
}

locals {
  permissions = {
    for idx, perm in var.permissions :
    "${perm.member}|${perm.role}" => perm
  }
  # This is a bit of a hack to get around the fact that the terraform does not
  # support the for_each loop with a list of maps, and on the user side, it
  # only makes sense to define the permissions like:
  #
  # permissions = [
  #   {
  #     member = "allUsers"
  #     role   = "roles/storage.objectViewer"
  #   }
  # ]
  #
  # Thus, we change it to a mapping of
  # {
  #   "allUsers|roles/storage.objectViewer" => {
  #     member = "allUsers"
  #     role   = "roles/storage.objectViewer"
  #   }
  # }
  #
  # And all of the sudden, terraform is happy with this structure...
  # Just remember to use the each.value to access the mapped "object"
}

resource "google_storage_bucket_iam_member" "permissions" {
  for_each   = local.permissions
  bucket     = google_storage_bucket.bucket.name
  member     = each.value.member
  role       = each.value.role
  depends_on = [google_storage_bucket.bucket]
}
