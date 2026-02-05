# VPC Network
resource "google_compute_network" "vpc" {
  project                 = var.project_id
  name                    = var.network_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

# Primary subnet for CloudRun Direct VPC egress
resource "google_compute_subnetwork" "primary" {
  project       = var.project_id
  name          = "${var.network_name}-primary"
  ip_cidr_range = var.primary_subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id

  # Enable private Google access for accessing GCP services
  private_ip_google_access = true
}

# Reserve IP range for Cloud SQL private service connection
# Using /20 (4096 IPs) instead of /24 (256 IPs) for future growth
resource "google_compute_global_address" "cloudsql_private_ip" {
  project       = var.project_id
  name          = "${var.network_name}-cloudsql-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 20 # 4096 IP addresses for Cloud SQL
  network       = google_compute_network.vpc.id
}

# Private VPC connection for Cloud SQL
resource "google_service_networking_connection" "cloudsql_private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.cloudsql_private_ip.name]

  depends_on = [google_compute_global_address.cloudsql_private_ip]
}

# Firewall rule: Allow internal traffic within VPC
# No target_tags - CloudRun v2 doesn't support network tags
resource "google_compute_firewall" "allow_internal" {
  project   = var.project_id
  name      = "${var.network_name}-allow-internal"
  network   = google_compute_network.vpc.name
  priority  = 1000
  direction = "INGRESS"

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/16"] # All internal subnets (current and future)
}

# Firewall rule: Allow SSH from IAP (for future Cloud SQL proxy or debugging)
resource "google_compute_firewall" "allow_iap_ssh" {
  project   = var.project_id
  name      = "${var.network_name}-allow-iap-ssh"
  network   = google_compute_network.vpc.name
  priority  = 1000
  direction = "INGRESS"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"] # IAP IP range
}
