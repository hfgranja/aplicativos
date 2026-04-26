resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 20

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      backup_retention_settings {
        retained_backups = 14
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    database_flags {
      name  = "max_connections"
      value = "200"
    }
  }

  deletion_protection = var.environment == "production"
  depends_on          = [google_service_networking_connection.private_vpc]
}

# Root user password
resource "google_sql_user" "root" {
  instance = google_sql_database_instance.main.name
  name     = "postgres"
  password = var.db_password
}

# One database + user per service
locals {
  services_db = {
    "identity"     = "pec_identity"
    "school"       = "pec_school"
    "observation"  = "pec_observation"
    "audio"        = "pec_audio"
    "transcription" = "pec_transcription"
    "ai_feedback"  = "pec_ai_feedback"
    "feedback"     = "pec_feedback"
    "pdf"          = "pec_pdf"
    "audit"        = "pec_audit"
    "consent"      = "pec_consent"
  }
}

resource "google_sql_database" "services" {
  for_each = local.services_db
  instance = google_sql_database_instance.main.name
  name     = each.value
}

resource "google_sql_user" "services" {
  for_each = local.services_db
  instance = google_sql_database_instance.main.name
  name     = "pec_${each.key}"
  password = lookup(var.db_service_passwords, each.key, var.db_password)
}
