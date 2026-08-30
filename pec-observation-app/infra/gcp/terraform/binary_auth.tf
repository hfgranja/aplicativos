# ── Binary Authorization ──────────────────────────────────────────────────────
# Garante que apenas imagens assinadas pela Cloud Build SA sejam deployadas.
# Habilitado APENAS em prod (enable_binary_auth = true).
#
# Fluxo: Cloud Build assina a imagem com Attestor → Cloud Run verifica assinatura

resource "google_binary_authorization_policy" "prod" {
  count = var.enable_binary_auth ? 1 : 0

  admission_whitelist_patterns {
    name_pattern = "gcr.io/google-containers/*"
  }
  admission_whitelist_patterns {
    name_pattern = "gcr.io/cloud-builders/*"
  }
  admission_whitelist_patterns {
    name_pattern = "gcr.io/google.com/cloudsdktool/*"
  }

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"

    require_attestations_by = [
      google_binary_authorization_attestor.cloud_build[0].name,
    ]
  }

  depends_on = [google_project_service.apis]
}

# Nota criptográfica — chave assimétrica para assinatura de imagens
resource "google_kms_key_ring" "binary_auth" {
  count = var.enable_binary_auth ? 1 : 0

  name     = "${var.app_name}-binary-auth-keyring"
  location = "global"
}

resource "google_kms_crypto_key" "binary_auth" {
  count = var.enable_binary_auth ? 1 : 0

  name     = "${var.app_name}-binary-auth-key"
  key_ring = google_kms_key_ring.binary_auth[0].id
  purpose  = "ASYMMETRIC_SIGN"

  version_template {
    algorithm = "RSA_SIGN_PKCS1_4096_SHA512"
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Attestor que valida imagens assinadas pelo Cloud Build
resource "google_binary_authorization_attestor" "cloud_build" {
  count = var.enable_binary_auth ? 1 : 0

  name = "${var.app_name}-build-attestor"

  attestation_authority_note {
    note_reference = google_container_analysis_note.attestor_note[0].name

    public_keys {
      id = google_kms_crypto_key_version.binary_auth_version[0].id
      pkix_public_key {
        public_key_pem      = google_kms_crypto_key_version.binary_auth_version[0].public_key[0].pem
        signature_algorithm = "RSA_PSS_4096_SHA512"
      }
    }
  }
}

resource "google_kms_crypto_key_version" "binary_auth_version" {
  count       = var.enable_binary_auth ? 1 : 0
  crypto_key  = google_kms_crypto_key.binary_auth[0].id
}

resource "google_container_analysis_note" "attestor_note" {
  count = var.enable_binary_auth ? 1 : 0

  name = "${var.app_name}-attestor-note"

  attestation_authority {
    hint {
      human_readable_name = "PEC Cloud Build Attestor — ${var.environment}"
    }
  }
}

# Permissão para Cloud Build assinar imagens
resource "google_kms_crypto_key_iam_member" "cloud_build_signer" {
  count = var.enable_binary_auth ? 1 : 0

  crypto_key_id = google_kms_crypto_key.binary_auth[0].id
  role          = "roles/cloudkms.signerVerifier"
  member        = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}
