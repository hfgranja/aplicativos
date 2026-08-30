# ── Customer-Managed Encryption Keys (CMEK) ───────────────────────────────────
# Criptografia adicional com chaves KMS gerenciadas pelo cliente.
# Habilitado APENAS em prod (enable_cmek = true).
# Aplica-se a: Cloud SQL + GCS bucket de áudios (dados mais sensíveis).

resource "google_kms_key_ring" "main" {
  count = var.enable_cmek ? 1 : 0

  name     = "${var.app_name}-cmek-keyring"
  location = var.region
  depends_on = [google_project_service.apis]
}

# Chave para Cloud SQL
resource "google_kms_crypto_key" "cloud_sql" {
  count    = var.enable_cmek ? 1 : 0
  name     = "${var.app_name}-cloudsql-key"
  key_ring = google_kms_key_ring.main[0].id

  rotation_period = "7776000s"  # 90 dias

  lifecycle {
    prevent_destroy = true
  }
}

# Chave para GCS (áudios e PDFs)
resource "google_kms_crypto_key" "gcs" {
  count    = var.enable_cmek ? 1 : 0
  name     = "${var.app_name}-gcs-key"
  key_ring = google_kms_key_ring.main[0].id

  rotation_period = "7776000s"  # 90 dias

  lifecycle {
    prevent_destroy = true
  }
}

# Permissão para Cloud SQL usar a chave CMEK
resource "google_kms_crypto_key_iam_member" "cloudsql_sa" {
  count         = var.enable_cmek ? 1 : 0
  crypto_key_id = google_kms_crypto_key.cloud_sql[0].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloud-sql.iam.gserviceaccount.com"
}

# Permissão para GCS usar a chave CMEK
resource "google_kms_crypto_key_iam_member" "gcs_sa" {
  count         = var.enable_cmek ? 1 : 0
  crypto_key_id = google_kms_crypto_key.gcs[0].id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:service-${data.google_project.project.number}@gs-project-accounts.iam.gserviceaccount.com"
}

# Outputs para referência em storage.tf e database.tf
locals {
  cmek_sql_key = var.enable_cmek ? google_kms_crypto_key.cloud_sql[0].id : null
  cmek_gcs_key = var.enable_cmek ? google_kms_crypto_key.gcs[0].id : null
}
