locals {
  all_domains = concat([var.domain], var.additional_domains)

  # Support both legacy single backend and new multi-backend approach
  # If cloudrun_backends is empty, use legacy variables
  use_legacy_config = length(var.cloudrun_backends) == 0

  # Build backends map from legacy or new config
  backends = local.use_legacy_config ? {
    "api" = {
      service_name = var.cloudrun_service_name
      location     = var.cloudrun_service_location
      path_prefix  = var.api_path_prefix
      priority     = 1
    }
  } : var.cloudrun_backends
}

# Enable required APIs
resource "google_project_service" "compute" {
  project            = var.google_project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# Global Static IP
resource "google_compute_global_address" "default" {
  project    = var.google_project_id
  name       = "${var.application_name}-global-ip"
  ip_version = "IPV4"
  depends_on = [google_project_service.compute]
}

# Backend Bucket for GCS Frontend (with CDN)
resource "google_compute_backend_bucket" "frontend" {
  project     = var.google_project_id
  name        = "${var.application_name}-frontend-bucket"
  bucket_name = var.frontend_bucket_name
  enable_cdn  = var.enable_cdn
  depends_on  = [google_project_service.compute]
}

# Serverless NEG for each Cloud Run backend
resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  for_each = local.backends

  project = var.google_project_id
  # Preserve legacy name for "api" backend to avoid recreation
  name                  = each.key == "api" ? "${var.application_name}-serverless-neg" : "${var.application_name}-${each.key}-neg"
  region                = each.value.location
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = each.value.service_name
  }

  depends_on = [google_project_service.compute]
}

# Global Backend Service for each Cloud Run backend
resource "google_compute_backend_service" "cloudrun_backends" {
  for_each = local.backends

  project               = var.google_project_id
  name                  = "${var.application_name}-${each.key}-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  protocol              = "HTTPS"

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg[each.key].id
  }

  depends_on = [google_project_service.compute]
}

# URL Map with Path-based Routing
resource "google_compute_url_map" "default" {
  project         = var.google_project_id
  name            = "${var.application_name}-global-lb"
  default_service = google_compute_backend_bucket.frontend.id

  host_rule {
    hosts        = local.all_domains
    path_matcher = "api-matcher"
  }

  path_matcher {
    name            = "api-matcher"
    default_service = google_compute_backend_bucket.frontend.id

    # Explicit path rules for each backend
    # API backend - higher priority paths should come first
    dynamic "path_rule" {
      for_each = { for k, v in local.backends : k => v }
      content {
        paths   = [path_rule.value.path_prefix]
        service = google_compute_backend_service.cloudrun_backends[path_rule.key].id
      }
    }
  }
}

# Managed SSL Certificate
resource "google_compute_managed_ssl_certificate" "default" {
  project = var.google_project_id
  name    = "${var.application_name}-global-cert"

  managed {
    domains = local.all_domains
  }
}

# HTTPS Proxy
resource "google_compute_target_https_proxy" "default" {
  project          = var.google_project_id
  name             = "${var.application_name}-global-https-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.default.id]
}

# HTTPS Forwarding Rule
resource "google_compute_global_forwarding_rule" "https" {
  project               = var.google_project_id
  name                  = "${var.application_name}-global-https-rule"
  target                = google_compute_target_https_proxy.default.id
  ip_address            = google_compute_global_address.default.id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# HTTP to HTTPS Redirect URL Map
resource "google_compute_url_map" "http_redirect" {
  project = var.google_project_id
  name    = "${var.application_name}-http-redirect"

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

# HTTP Proxy for Redirect
resource "google_compute_target_http_proxy" "redirect" {
  project = var.google_project_id
  name    = "${var.application_name}-global-http-proxy"
  url_map = google_compute_url_map.http_redirect.id
}

# HTTP Forwarding Rule (redirects to HTTPS)
resource "google_compute_global_forwarding_rule" "http" {
  project               = var.google_project_id
  name                  = "${var.application_name}-global-http-rule"
  target                = google_compute_target_http_proxy.redirect.id
  ip_address            = google_compute_global_address.default.id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL_MANAGED"
}

# Migration: Rename legacy resources to new map-based resources
moved {
  from = google_compute_region_network_endpoint_group.cloudrun_neg
  to   = google_compute_region_network_endpoint_group.cloudrun_neg["api"]
}

moved {
  from = google_compute_backend_service.api
  to   = google_compute_backend_service.cloudrun_backends["api"]
}
