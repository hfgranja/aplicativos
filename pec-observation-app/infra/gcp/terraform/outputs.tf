output "cloud_run_urls" {
  description = "Cloud Run service URLs"
  value = {
    ms_001_identity     = google_cloud_run_v2_service.ms["ms-001-identity"].uri
    ms_002_school       = google_cloud_run_v2_service.ms["ms-002-school"].uri
    ms_003_observation  = google_cloud_run_v2_service.ms["ms-003-observation"].uri
    ms_004_audio        = google_cloud_run_v2_service.ms["ms-004-audio-ingestion"].uri
    ms_005_transcription = google_cloud_run_v2_service.ms["ms-005-transcription"].uri
    ms_006_ai_feedback  = google_cloud_run_v2_service.ms["ms-006-ai-feedback"].uri
    ms_007_feedback     = google_cloud_run_v2_service.ms["ms-007-feedback"].uri
    ms_008_pdf          = google_cloud_run_v2_service.ms["ms-008-pdf-export"].uri
    ms_009_audit        = google_cloud_run_v2_service.ms["ms-009-audit"].uri
    ms_010_consent      = google_cloud_run_v2_service.ms["ms-010-consent"].uri
  }
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "redis_host" {
  description = "Memorystore Redis host"
  value       = google_redis_instance.main.host
  sensitive   = true
}

output "artifact_registry_url" {
  description = "Docker image registry base URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "audio_bucket_name" {
  description = "GCS audio uploads bucket"
  value       = google_storage_bucket.audio_uploads.name
}

output "pdf_bucket_name" {
  description = "GCS PDF exports bucket"
  value       = google_storage_bucket.pdf_exports.name
}

output "service_account_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}

output "vpc_connector_name" {
  description = "Serverless VPC access connector"
  value       = google_vpc_access_connector.main.name
}
