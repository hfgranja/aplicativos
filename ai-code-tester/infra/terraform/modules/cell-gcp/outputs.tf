output "gke_cluster_name" {
  value = google_container_cluster.gke.name
}

output "artifact_registry" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/ait"
}

output "gcs_assets_bucket" {
  value = google_storage_bucket.assets.name
}
