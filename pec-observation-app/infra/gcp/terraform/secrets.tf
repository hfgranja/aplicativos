locals {
  secrets = {
    jwt-secret-key      = var.jwt_secret_key
    db-password         = var.db_password
    minio-access-key    = var.minio_access_key != "" ? var.minio_access_key : google_storage_hmac_key.service_account_key.access_id
    minio-secret-key    = var.minio_secret_key != "" ? var.minio_secret_key : google_storage_hmac_key.service_account_key.secret
  }
}

resource "google_secret_manager_secret" "secrets" {
  for_each  = local.secrets
  secret_id = "${var.app_name}-${each.key}"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "secrets" {
  for_each    = local.secrets
  secret      = google_secret_manager_secret.secrets[each.key].id
  secret_data = each.value
}
