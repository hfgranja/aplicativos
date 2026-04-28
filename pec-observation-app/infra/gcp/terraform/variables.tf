variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "southamerica-east1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "app_name" {
  type    = string
  default = "pec-obs"
}

# ── Database ─────────────────────────────────────────────────────────────────

variable "db_tier" {
  description = "Cloud SQL tier (db-g1-small = ~$10/mo, db-custom-2-4096 = ~$70/mo)"
  type        = string
  default     = "db-custom-2-4096"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_service_passwords" {
  description = "Per-service DB passwords (key = service short name, e.g. identity)"
  type        = map(string)
  sensitive   = true
  default     = {}
}

# ── Auth ─────────────────────────────────────────────────────────────────────

variable "jwt_secret_key" {
  description = "JWT HS256 secret (min 32 chars — run: openssl rand -hex 32)"
  type        = string
  sensitive   = true
}

# ── Storage ──────────────────────────────────────────────────────────────────

variable "audio_retention_days" {
  type    = number
  default = 7
}

variable "minio_access_key" {
  description = "GCS HMAC access key (S3-compatible)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "minio_secret_key" {
  description = "GCS HMAC secret key (S3-compatible)"
  type        = string
  sensitive   = true
  default     = ""
}

# ── Ollama VM ─────────────────────────────────────────────────────────────────

variable "ollama_machine_type" {
  description = "GCE machine type for the Ollama VM"
  type        = string
  default     = "e2-standard-4"   # 4 vCPU, 16 GB RAM — ~$100/mo in SA-east1
}

variable "ollama_model" {
  description = "Ollama generative model"
  type        = string
  default     = "llama3.2"
}

variable "ollama_embedding_model" {
  description = "Ollama embedding model for MS-013/MS-014"
  type        = string
  default     = "nomic-embed-text"
}

variable "pec_model_name" {
  description = "Name of the continuously trained Ollama model"
  type        = string
  default     = "pec-pedagogo"
}

# ── Whisper ──────────────────────────────────────────────────────────────────

variable "whisper_model_size" {
  type    = string
  default = "small"
}

# ── Cloud Run scaling ─────────────────────────────────────────────────────────

variable "cloud_run_min_instances" {
  description = "Default minimum instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  type    = number
  default = 10
}

variable "cloud_run_min_instances_override" {
  description = "Per-service min-instance overrides (service name → count)"
  type        = map(number)
  default = {
    "ms-001-identity"    = 1   # identity always warm
    "ms-003-observation" = 1
  }
}

variable "cloud_run_max_instances_override" {
  description = "Per-service max-instance overrides"
  type        = map(number)
  default = {
    "ms-005-transcription" = 3   # CPU-bound, cap instances
    "ms-006-ai-feedback"   = 2
    "ms-013-learning"      = 2
    "ms-014-evaluator"     = 2
  }
}

variable "cloud_run_cpu" {
  type    = string
  default = "1"
}

variable "cloud_run_memory" {
  type    = string
  default = "512Mi"
}

variable "cloud_run_cpu_override" {
  description = "Per-service CPU overrides"
  type        = map(string)
  default = {
    "ms-005-transcription" = "4"
    "ms-006-ai-feedback"   = "2"
    "ms-013-learning"      = "2"
    "ms-014-evaluator"     = "2"
    "ms-012-best-practices"= "2"
  }
}

variable "cloud_run_memory_override" {
  description = "Per-service memory overrides"
  type        = map(string)
  default = {
    "ms-005-transcription"  = "4Gi"
    "ms-006-ai-feedback"    = "1Gi"
    "ms-013-learning"       = "1Gi"
    "ms-014-evaluator"      = "1Gi"
    "ms-012-best-practices" = "2Gi"
  }
}

# ── Monitoring ────────────────────────────────────────────────────────────────

variable "alert_email" {
  description = "Email for Cloud Monitoring alerts"
  type        = string
  default     = "henriquef.granja@gmail.com"
}

variable "quality_alert_threshold" {
  description = "Model quality score below which an alert fires (MS-014)"
  type        = number
  default     = 0.60
}
