# ── Cloud DLP — Proteção contra vazamento de PII em logs ─────────────────────
# Escaneia logs do Cloud Run em busca de PII acidentalmente logado.
# Habilitado apenas em PRODUÇÃO (enable_cmek = true como proxy para prod).
# Detecta: CPF, e-mail, nome completo, número de telefone BR.

resource "google_data_loss_prevention_inspect_template" "pii_scan" {
  count = var.enable_cmek ? 1 : 0    # Produção = enable_cmek = true

  parent       = "projects/${var.project_id}"
  display_name = "PEC PII Inspection Template"
  description  = "Detecta PII em logs do Cloud Run — CPF, e-mail, nomes, telefone BR"

  inspect_config {
    info_types {
      name = "BRAZIL_CPF_NUMBER"
    }
    info_types {
      name = "EMAIL_ADDRESS"
    }
    info_types {
      name = "PERSON_NAME"
    }
    info_types {
      name = "PHONE_NUMBER"
    }

    min_likelihood = "LIKELY"

    limits {
      max_findings_per_item    = 100
      max_findings_per_request = 1000
    }
  }

  depends_on = [google_project_service.apis]
}

# Job trigger — escaneia BigQuery export de logs diariamente
resource "google_data_loss_prevention_job_trigger" "log_pii_scan" {
  count = var.enable_cmek ? 1 : 0

  parent       = "projects/${var.project_id}"
  display_name = "PEC Cloud Run Log PII Scan"
  description  = "Escaneia logs exportados para BQ buscando PII não mascarado"
  status       = "HEALTHY"

  triggers {
    schedule {
      recurrence_period_duration = "86400s"   # Diário
    }
  }

  inspect_job {
    inspect_template_name = google_data_loss_prevention_inspect_template.pii_scan[0].name

    storage_config {
      big_query_options {
        table_reference {
          project_id = var.project_id
          dataset_id = "pec_logs"
          table_id   = "cloudrun_logs"
        }
        rows_limit        = 10000
        sample_method     = "RANDOM_START"
      }
    }

    actions {
      # Publica descobertas no Security Command Center + alerta por e-mail
      publish_findings_to_cloud_data_catalog {}
    }

    actions {
      # Notifica via Pub/Sub para acionar alerta
      pub_sub {
        topic = "projects/${var.project_id}/topics/${var.app_name}-dlp-findings"
      }
    }
  }

  depends_on = [google_data_loss_prevention_inspect_template.pii_scan]
}

# Exportação de logs para BigQuery (necessária para o DLP job)
resource "google_logging_project_sink" "cloudrun_to_bq" {
  count = var.enable_cmek ? 1 : 0

  name        = "${var.app_name}-cloudrun-logs-bq"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/pec_logs"
  filter      = "resource.type=\"cloud_run_revision\" severity>=WARNING"

  unique_writer_identity = true
}

resource "google_bigquery_dataset" "pec_logs" {
  count = var.enable_cmek ? 1 : 0

  dataset_id  = "pec_logs"
  location    = var.region
  description = "Cloud Run logs exportados para análise DLP — PEC ${var.environment}"

  labels = {
    environment         = var.environment
    data_classification = "logs"
  }
}

# Permissão para o sink escrever no BigQuery
resource "google_bigquery_dataset_iam_member" "log_sink_writer" {
  count   = var.enable_cmek ? 1 : 0
  dataset_id = google_bigquery_dataset.pec_logs[0].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.cloudrun_to_bq[0].writer_identity
}
