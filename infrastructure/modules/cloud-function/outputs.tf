output "function_uris" {
  description = "Map of function name to URI"
  value = {
    for name, fn in google_cloudfunctions2_function.function : name => fn.service_config[0].uri
  }
}

output "service_account_emails" {
  description = "Map of function name to service account email"
  value = {
    for name, sa in google_service_account.sa : name => sa.email
  }
}
