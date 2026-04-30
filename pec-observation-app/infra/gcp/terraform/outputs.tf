output "web_app_url" {
  description = "Public URL of the React web application"
  value       = google_cloud_run_v2_service.web_app.uri
}

output "cloud_run_urls" {
  description = "All microservice Cloud Run URLs"
  value = {
    ms_001_identity       = google_cloud_run_v2_service.ms["ms-001-identity"].uri
    ms_002_school         = google_cloud_run_v2_service.ms["ms-002-school"].uri
    ms_003_observation    = google_cloud_run_v2_service.ms["ms-003-observation"].uri
    ms_004_audio          = google_cloud_run_v2_service.ms["ms-004-audio-ingestion"].uri
    ms_005_transcription  = google_cloud_run_v2_service.ms["ms-005-transcription"].uri
    ms_006_ai_feedback    = google_cloud_run_v2_service.ms["ms-006-ai-feedback"].uri
    ms_007_feedback       = google_cloud_run_v2_service.ms["ms-007-feedback"].uri
    ms_008_pdf            = google_cloud_run_v2_service.ms["ms-008-pdf-export"].uri
    ms_009_audit          = google_cloud_run_v2_service.ms["ms-009-audit"].uri
    ms_010_consent        = google_cloud_run_v2_service.ms["ms-010-consent"].uri
    ms_011_knowledge      = google_cloud_run_v2_service.ms["ms-011-knowledge"].uri
    ms_012_best_practices = google_cloud_run_v2_service.ms["ms-012-best-practices"].uri
    ms_013_learning       = google_cloud_run_v2_service.ms["ms-013-learning"].uri
    ms_014_evaluator      = google_cloud_run_v2_service.ms["ms-014-evaluator"].uri
    ms_015_mcp            = google_cloud_run_v2_service.ms["ms-015-mcp"].uri
  }
}

output "mcp_server_url" {
  description = "MCP server endpoint — use as remote MCP server in Claude Desktop"
  value       = "${google_cloud_run_v2_service.ms["ms-015-mcp"].uri}/mcp"
}

output "ollama_internal_ip" {
  description = "Ollama VM internal IP (VPC only)"
  value       = google_compute_instance.ollama.network_interface[0].network_ip
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "redis_host" {
  value     = google_redis_instance.main.host
  sensitive = true
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.repository_id}"
}

output "audio_bucket_name" {
  value = google_storage_bucket.audio_uploads.name
}

output "pdf_bucket_name" {
  value = google_storage_bucket.pdf_exports.name
}

output "service_account_email" {
  value = google_service_account.cloud_run.email
}

output "ssh_to_ollama" {
  description = "Command to SSH into the Ollama VM via IAP"
  value       = "gcloud compute ssh ${google_compute_instance.ollama.name} --zone=${var.region}-b --tunnel-through-iap --project=${var.project_id}"
}
