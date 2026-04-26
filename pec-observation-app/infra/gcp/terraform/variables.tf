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
  description = "Deployment environment (production, staging)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Application name prefix"
  type        = string
  default     = "pec-obs"
}

# Database
variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-g1-small"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_service_passwords" {
  description = "Per-service DB passwords map"
  type        = map(string)
  sensitive   = true
  default     = {}
}

# Auth
variable "jwt_secret_key" {
  description = "HS256 secret key for JWT signing (min 32 chars)"
  type        = string
  sensitive   = true
}

# Storage
variable "audio_retention_days" {
  description = "Days to retain audio files (LGPD)"
  type        = number
  default     = 7
}

# MinIO / GCS
variable "minio_access_key" {
  description = "GCS HMAC access key (for S3-compatible API)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "minio_secret_key" {
  description = "GCS HMAC secret key (for S3-compatible API)"
  type        = string
  sensitive   = true
  default     = ""
}

# Ollama / LLM
variable "ollama_model" {
  description = "Ollama model name"
  type        = string
  default     = "llama3.2"
}

# Whisper
variable "whisper_model_size" {
  description = "faster-whisper model size"
  type        = string
  default     = "small"
}

# Cloud Run scaling
variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances per service"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Maximum Cloud Run instances per service"
  type        = number
  default     = 10
}

variable "cloud_run_cpu" {
  description = "CPU allocation per Cloud Run instance"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Memory allocation per Cloud Run instance"
  type        = string
  default     = "512Mi"
}

# Notification
variable "alert_email" {
  description = "Email for Cloud Monitoring alerts"
  type        = string
  default     = ""
}
