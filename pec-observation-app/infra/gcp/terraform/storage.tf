resource "google_storage_bucket" "audio_uploads" {
  name                        = "${var.project_id}-${var.app_name}-audio"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  # CMEK — Customer-Managed Encryption Key (prod only)
  dynamic "encryption" {
    for_each = var.enable_cmek ? [1] : []
    content {
      default_kms_key_name = local.cmek_gcs_key
    }
  }

  lifecycle_rule {
    condition { age = var.audio_retention_days }
    action { type = "Delete" }
  }

  versioning {
    enabled = false
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "PUT", "HEAD"]
    response_header = ["Content-Type", "Content-MD5"]
    max_age_seconds = 3600
  }

  # Audit logging para compliance LGPD
  labels = {
    data_classification = "sensitive_personal_data"
    environment         = var.environment
    lgpd_retention      = "audio_${var.audio_retention_days}d"
  }

  depends_on = var.enable_cmek ? [google_kms_crypto_key_iam_member.gcs_sa] : []
}

resource "google_storage_bucket" "pdf_exports" {
  name                        = "${var.project_id}-${var.app_name}-pdf"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  dynamic "encryption" {
    for_each = var.enable_cmek ? [1] : []
    content {
      default_kms_key_name = local.cmek_gcs_key
    }
  }

  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }

  labels = {
    data_classification = "output_data"
    environment         = var.environment
  }

  depends_on = var.enable_cmek ? [google_kms_crypto_key_iam_member.gcs_sa] : []
}

# HMAC key for S3-compatible API (boto3 endpoint: https://storage.googleapis.com)
resource "google_storage_hmac_key" "service_account_key" {
  service_account_email = google_service_account.cloud_run.email
  depends_on            = [google_service_account.cloud_run]
}
