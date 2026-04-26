resource "google_redis_instance" "main" {
  name           = "${var.app_name}-redis"
  tier           = var.environment == "production" ? "STANDARD_HA" : "BASIC"
  memory_size_gb = 1
  region         = var.region

  location_id             = "${var.region}-a"
  alternative_location_id = var.environment == "production" ? "${var.region}-b" : null

  authorized_network = google_compute_network.main.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"

  persistence_config {
    persistence_mode    = "RDB"
    rdb_snapshot_period = "TWENTY_FOUR_HOURS"
  }

  depends_on = [google_service_networking_connection.private_vpc]
}
