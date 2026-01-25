output "bucket_name" {
  description = "The name of the frontend bucket"
  value       = google_storage_bucket.frontend.name
}
