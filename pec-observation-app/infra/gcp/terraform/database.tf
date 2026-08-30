resource "google_sql_database_instance" "main" {
  name             = "${var.app_name}-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  # CMEK — Customer-Managed Encryption Key (prod only)
  encryption_key_name = var.enable_cmek ? local.cmek_sql_key : null

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "production" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 30

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    database_flags {
      name  = "max_connections"
      value = "300"
    }
    # pgvector requires shared_preload_libraries — included by default in Cloud SQL PG15

    user_labels = {
      environment         = var.environment
      data_classification = "sensitive_personal_data"
    }
  }

  deletion_protection = var.environment == "production"
  depends_on = concat(
    [google_service_networking_connection.private_vpc],
    var.enable_cmek ? [google_kms_crypto_key_iam_member.cloudsql_sa[0]] : [],
  )
}

resource "google_sql_user" "root" {
  instance = google_sql_database_instance.main.name
  name     = "postgres"
  password = var.db_password
}

# ── All 14 service databases ─────────────────────────────────────────────────

locals {
  services_db = {
    "identity"       = "pec_identity"
    "school"         = "pec_school"
    "observation"    = "pec_observation"
    "audio"          = "pec_audio"
    "transcription"  = "pec_transcription"
    "ai_feedback"    = "pec_ai_feedback"
    "feedback"       = "pec_feedback"
    "pdf"            = "pec_pdf"
    "audit"          = "pec_audit"
    "consent"        = "pec_consent"
    "knowledge"      = "pec_knowledge"
    "best_practices" = "pec_best_practices"
    "learning"       = "pec_learning"
    "evaluator"      = "pec_evaluator"
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

# ── pgvector extension for pec_learning (MS-013) ─────────────────────────────
# Cloud SQL PG15 ships with the vector extension; we enable it via a null_resource
# that runs a SQL command after the database exists.

resource "null_resource" "pgvector_extension" {
  triggers = {
    db_instance = google_sql_database_instance.main.id
    db_name     = google_sql_database.services["learning"].name
  }

  provisioner "local-exec" {
    command = <<-CMD
      gcloud sql connect ${google_sql_database_instance.main.name} \\
        --user=postgres \\
        --database=pec_learning \\
        --project=${var.project_id} \\
        --quiet \\
        <<< "CREATE EXTENSION IF NOT EXISTS vector;"
    CMD
  }

  depends_on = [
    google_sql_database.services,
    google_sql_user.root,
    google_project_service.apis,
  ]
}
