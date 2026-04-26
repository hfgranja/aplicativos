resource "google_service_account" "cloud_run" {
  account_id   = "${var.app_name}-run-sa"
  display_name = "PEC Observation Cloud Run Service Account"
}

locals {
  sa_roles = [
    "roles/cloudsql.client",
    "roles/redis.viewer",
    "roles/storage.objectAdmin",
    "roles/secretmanager.secretAccessor",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/artifactregistry.reader",
  ]
}

resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset(local.sa_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Cloud Build service account can deploy to Cloud Run
resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${data.google_project.main.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${data.google_project.main.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${data.google_project.main.number}@cloudbuild.gserviceaccount.com"
}

data "google_project" "main" {
  project_id = var.project_id
}

# Public invoke for all Cloud Run services (internal load balancer in production)
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  for_each = toset(local.service_names)
  project  = var.project_id
  location = var.region
  name     = "${var.app_name}-${each.value}"
  role     = "roles/run.invoker"
  member   = "allUsers"

  depends_on = [google_cloud_run_v2_service.ms]
}
