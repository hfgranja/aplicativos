resource "google_compute_network" "main" {
  name                    = "${var.app_name}-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "main" {
  name          = "${var.app_name}-subnet"
  ip_cidr_range = "10.10.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_range" {
  name          = "${var.app_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
  depends_on              = [google_project_service.apis]
}

# Serverless VPC connector — Cloud Run → Memorystore Redis (VPC-only)
resource "google_vpc_access_connector" "main" {
  provider      = google-beta
  name          = "${var.app_name}-connector"
  region        = var.region
  network       = google_compute_network.main.name
  ip_cidr_range = "10.10.1.0/28"
  min_instances = 2
  max_instances = 10
  depends_on    = [google_project_service.apis]
}
