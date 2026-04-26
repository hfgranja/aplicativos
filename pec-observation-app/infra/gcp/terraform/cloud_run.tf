locals {
  registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"

  service_names = [
    "ms-001-identity",
    "ms-002-school",
    "ms-003-observation",
    "ms-004-audio-ingestion",
    "ms-005-transcription",
    "ms-006-ai-feedback",
    "ms-007-feedback",
    "ms-008-pdf-export",
    "ms-009-audit",
    "ms-010-consent",
  ]

  # Per-service DB names and user names
  service_db_map = {
    "ms-001-identity"       = { db = "pec_identity",     user = "pec_identity" }
    "ms-002-school"         = { db = "pec_school",       user = "pec_school" }
    "ms-003-observation"    = { db = "pec_observation",  user = "pec_observation" }
    "ms-004-audio-ingestion"= { db = "pec_audio",        user = "pec_audio" }
    "ms-005-transcription"  = { db = "pec_transcription",user = "pec_transcription" }
    "ms-006-ai-feedback"    = { db = "pec_ai_feedback",  user = "pec_ai_feedback" }
    "ms-007-feedback"       = { db = "pec_feedback",     user = "pec_feedback" }
    "ms-008-pdf-export"     = { db = "pec_pdf",          user = "pec_pdf" }
    "ms-009-audit"          = { db = "pec_audit",        user = "pec_audit" }
    "ms-010-consent"        = { db = "pec_consent",      user = "pec_consent" }
  }

  # Services that consume Redis Streams (all run a background thread)
  redis_consumers = [
    "ms-005-transcription",
    "ms-006-ai-feedback",
    "ms-007-feedback",
    "ms-008-pdf-export",
    "ms-009-audit",
    "ms-010-consent",
  ]

  # Common environment variables for every service
  common_env = [
    { name = "ENVIRONMENT",             value = var.environment },
    { name = "OTEL_EXPORTER_ENABLED",  value = "true" },
    { name = "REDIS_URL",              value = "redis://${google_redis_instance.main.host}:6379/0" },
    { name = "MINIO_ENDPOINT",         value = "https://storage.googleapis.com" },
    { name = "MINIO_SECURE",           value = "true" },
    { name = "AUDIO_BUCKET",           value = google_storage_bucket.audio_uploads.name },
    { name = "PDF_BUCKET",             value = google_storage_bucket.pdf_exports.name },
    { name = "AUDIO_RETENTION_DAYS",   value = tostring(var.audio_retention_days) },
    { name = "WHISPER_MODEL_SIZE",     value = var.whisper_model_size },
    { name = "OLLAMA_MODEL",           value = var.ollama_model },
  ]
}

resource "google_cloud_run_v2_service" "ms" {
  for_each = toset(local.service_names)

  name     = "${var.app_name}-${each.value}"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = var.cloud_run_min_instances
      max_instance_count = var.cloud_run_max_instances
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    containers {
      image = "${local.registry}/${each.value}:latest"

      resources {
        limits = {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      # Cloud SQL socket mount
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      # Common env
      dynamic "env" {
        for_each = local.common_env
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      # Per-service DATABASE_URL via Cloud SQL Unix socket
      env {
        name = "DATABASE_URL"
        value = join("", [
          "postgresql+psycopg2://",
          local.service_db_map[each.value].user,
          ":$(DB_PASSWORD)@/",
          local.service_db_map[each.value].db,
          "?host=/cloudsql/",
          google_sql_database_instance.main.connection_name,
        ])
      }

      # Secrets
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["jwt-secret-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["db-password"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MINIO_ACCESS_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["minio-access-key"].secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "MINIO_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secrets["minio-secret-key"].secret_id
            version = "latest"
          }
        }
      }

      liveness_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 15
        period_seconds        = 30
        failure_threshold     = 3
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 12
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_sql_database_instance.main,
    google_redis_instance.main,
    google_secret_manager_secret_version.secrets,
    google_service_account.cloud_run,
    google_project_iam_member.cloud_run_roles,
  ]
}
