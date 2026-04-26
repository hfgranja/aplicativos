resource "google_artifact_registry_repository" "main" {
  repository_id = "${var.app_name}-images"
  location      = var.region
  format        = "DOCKER"
  description   = "PEC Observation App microservice images"
  depends_on    = [google_project_service.apis]
}
