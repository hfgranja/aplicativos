locals {
  registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"

  # ── All 14 microservices ────────────────────────────────────────────────────
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
    "ms-011-knowledge",
    "ms-012-best-practices",
    "ms-013-learning",
    "ms-014-evaluator",
  ]

  # Per-service DB names and users
  service_db_map = {
    "ms-001-identity"        = { db = "pec_identity",      user = "pec_identity" }
    "ms-002-school"          = { db = "pec_school",        user = "pec_school" }
    "ms-003-observation"     = { db = "pec_observation",   user = "pec_observation" }
    "ms-004-audio-ingestion" = { db = "pec_audio",         user = "pec_audio" }
    "ms-005-transcription"   = { db = "pec_transcription", user = "pec_transcription" }
    "ms-006-ai-feedback"     = { db = "pec_ai_feedback",   user = "pec_ai_feedback" }
    "ms-007-feedback"        = { db = "pec_feedback",      user = "pec_feedback" }
    "ms-008-pdf-export"      = { db = "pec_pdf",           user = "pec_pdf" }
    "ms-009-audit"           = { db = "pec_audit",         user = "pec_audit" }
    "ms-010-consent"         = { db = "pec_consent",       user = "pec_consent" }
    "ms-011-knowledge"       = { db = "pec_knowledge",     user = "pec_knowledge" }
    "ms-012-best-practices"  = { db = "pec_best_practices",user = "pec_best_practices" }
    "ms-013-learning"        = { db = "pec_learning",      user = "pec_learning" }
    "ms-014-evaluator"       = { db = "pec_evaluator",     user = "pec_evaluator" }
  }

  # Services that need Ollama access (internal VM IP)
  ollama_consumers = [
    "ms-005-transcription",
    "ms-006-ai-feedback",
    "ms-013-learning",
    "ms-014-evaluator",
  ]

  # Inter-service URLs (Cloud Run internal DNS)
  svc_url = {
    identity       = "https://${var.app_name}-ms-001-identity-${data.google_project.project.number}.${var.region}.run.app"
    knowledge      = "https://${var.app_name}-ms-011-knowledge-${data.google_project.project.number}.${var.region}.run.app"
    learning       = "https://${var.app_name}-ms-013-learning-${data.google_project.project.number}.${var.region}.run.app"
    evaluator      = "https://${var.app_name}-ms-014-evaluator-${data.google_project.project.number}.${var.region}.run.app"
    audio          = "https://${var.app_name}-ms-004-audio-ingestion-${data.google_project.project.number}.${var.region}.run.app"
    transcription  = "https://${var.app_name}-ms-005-transcription-${data.google_project.project.number}.${var.region}.run.app"
  }

  # Common environment variables
  common_env = [
    { name = "ENVIRONMENT",            value = var.environment },
    { name = "OTEL_EXPORTER_ENABLED",  value = "true" },
    { name = "REDIS_URL",              value = "redis://${google_redis_instance.main.host}:6379/0" },
    { name = "MINIO_ENDPOINT",         value = "https://storage.googleapis.com" },
    { name = "MINIO_SECURE",           value = "true" },
    { name = "AUDIO_BUCKET",           value = google_storage_bucket.audio_uploads.name },
    { name = "PDF_BUCKET",             value = google_storage_bucket.pdf_exports.name },
    { name = "AUDIO_RETENTION_DAYS",   value = tostring(var.audio_retention_days) },
    { name = "WHISPER_MODEL_SIZE",     value = var.whisper_model_size },
    { name = "OLLAMA_BASE_URL",        value = "http://${google_compute_instance.ollama.network_interface[0].network_ip}:11434" },
    { name = "OLLAMA_MODEL",           value = var.ollama_model },
    { name = "OLLAMA_EMBEDDING_MODEL", value = var.ollama_embedding_model },
    { name = "PEC_MODEL_NAME",         value = var.pec_model_name },
  ]
}

data "google_project" "project" {}

# ── Microservices (Cloud Run v2) ─────────────────────────────────────────────

resource "google_cloud_run_v2_service" "ms" {
  for_each = toset(local.service_names)

  name     = "${var.app_name}-${each.value}"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email

    scaling {
      min_instance_count = lookup(var.cloud_run_min_instances_override, each.value, var.cloud_run_min_instances)
      max_instance_count = lookup(var.cloud_run_max_instances_override, each.value, var.cloud_run_max_instances)
    }

    vpc_access {
      connector = google_vpc_access_connector.main.id
      egress    = "ALL_TRAFFIC"
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
          cpu    = lookup(var.cloud_run_cpu_override,    each.value, var.cloud_run_cpu)
          memory = lookup(var.cloud_run_memory_override, each.value, var.cloud_run_memory)
        }
        cpu_idle          = !contains(["ms-005-transcription", "ms-006-ai-feedback", "ms-013-learning"], each.value)
        startup_cpu_boost = true
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      # Common env vars
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

      # Inter-service routing
      env {
        name  = "KNOWLEDGE_SERVICE_URL"
        value = local.svc_url.knowledge
      }
      env {
        name  = "LEARNING_SERVICE_URL"
        value = local.svc_url.learning
      }
      env {
        name  = "EVALUATOR_SERVICE_URL"
        value = local.svc_url.evaluator
      }
      env {
        name  = "AUDIO_SERVICE_URL"
        value = local.svc_url.audio
      }
      env {
        name  = "TRANSCRIPTION_SERVICE_URL"
        value = local.svc_url.transcription
      }

      # ── Secrets ────────────────────────────────────────────────────────────
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
        http_get { path = "/health" }
        initial_delay_seconds = 20
        period_seconds        = 30
        failure_threshold     = 3
      }
      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 20
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
    google_compute_instance.ollama,
  ]
}

# Allow unauthenticated access (gateway enforces auth via JWT)
resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = toset(local.service_names)
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ms[each.value].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Web App (React SPA) ───────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "web_app" {
  name     = "${var.app_name}-web-app"
  location = var.region

  template {
    service_account = google_service_account.cloud_run.email
    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
    containers {
      image = "${local.registry}/web-app:latest"
      resources {
        limits = { cpu = "1", memory = "256Mi" }
        cpu_idle = true
      }
      # The Nginx gateway needs backend URLs to proxy to
      dynamic "env" {
        for_each = {
          IDENTITY_URL       = google_cloud_run_v2_service.ms["ms-001-identity"].uri
          SCHOOL_URL         = google_cloud_run_v2_service.ms["ms-002-school"].uri
          OBSERVATION_URL    = google_cloud_run_v2_service.ms["ms-003-observation"].uri
          AUDIO_URL          = google_cloud_run_v2_service.ms["ms-004-audio-ingestion"].uri
          FEEDBACK_URL       = google_cloud_run_v2_service.ms["ms-007-feedback"].uri
          KNOWLEDGE_URL      = google_cloud_run_v2_service.ms["ms-011-knowledge"].uri
          BEST_PRACTICES_URL = google_cloud_run_v2_service.ms["ms-012-best-practices"].uri
          EVALUATOR_URL      = google_cloud_run_v2_service.ms["ms-014-evaluator"].uri
        }
        content {
          name  = env.key
          value = env.value
        }
      }
      liveness_probe {
        http_get { path = "/" }
        period_seconds = 30
      }
    }
  }
  depends_on = [google_cloud_run_v2_service.ms]
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web_app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
