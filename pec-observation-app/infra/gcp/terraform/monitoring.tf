# ── Cloud Monitoring — Alerting ───────────────────────────────────────────────
# Alerts for: model quality degradation, Cloud Run errors, high latency

resource "google_monitoring_notification_channel" "email" {
  display_name = "PEC Alerts Email"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
  depends_on = [google_project_service.apis]
}

# ── Alert: Cloud Run 5xx errors (any service) ────────────────────────────────

resource "google_monitoring_alert_policy" "cloud_run_errors" {
  display_name = "PEC — Cloud Run 5xx errors"
  combiner     = "OR"

  conditions {
    display_name = "5xx error rate > 5% for 5 min"
    condition_threshold {
      filter = <<-FILTER
        resource.type = "cloud_run_revision"
        AND metric.type = "run.googleapis.com/request_count"
        AND metric.labels.response_code_class = "5xx"
      FILTER
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      duration        = "300s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  alert_strategy {
    auto_close = "1800s"
  }
}

# ── Alert: Cloud Run high latency ────────────────────────────────────────────

resource "google_monitoring_alert_policy" "high_latency" {
  display_name = "PEC — API latency p99 > 5s"
  combiner     = "OR"

  conditions {
    display_name = "p99 latency > 5000ms"
    condition_threshold {
      filter = <<-FILTER
        resource.type = "cloud_run_revision"
        AND metric.type = "run.googleapis.com/request_latencies"
      FILTER
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      duration        = "120s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MAX"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  alert_strategy {
    auto_close = "3600s"
  }
}

# ── Alert: Ollama VM down ─────────────────────────────────────────────────────

resource "google_monitoring_alert_policy" "ollama_vm_down" {
  display_name = "PEC — Ollama VM unreachable"
  combiner     = "OR"

  conditions {
    display_name = "Ollama VM CPU = 0 for 10 min (likely stopped)"
    condition_threshold {
      filter = <<-FILTER
        resource.type = "gce_instance"
        AND resource.labels.instance_id = "${google_compute_instance.ollama.instance_id}"
        AND metric.type = "compute.googleapis.com/instance/cpu/utilization"
      FILTER
      comparison      = "COMPARISON_LT"
      threshold_value = 0.001
      duration        = "600s"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  alert_strategy {
    auto_close = "1800s"
  }
}

# ── Alert: Cloud SQL storage > 80% ───────────────────────────────────────────

resource "google_monitoring_alert_policy" "db_storage" {
  display_name = "PEC — Cloud SQL storage > 80%"
  combiner     = "OR"

  conditions {
    display_name = "DB disk usage > 80%"
    condition_threshold {
      filter = <<-FILTER
        resource.type = "cloudsql_database"
        AND metric.type = "cloudsql.googleapis.com/database/disk/utilization"
      FILTER
      comparison      = "COMPARISON_GT"
      threshold_value = 0.80
      duration        = "300s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

# ── Custom metric: model quality from MS-014 ─────────────────────────────────
# MS-014 exposes /metrics — Cloud Run logs include quality_score.
# We create a log-based metric to track it.

resource "google_logging_metric" "model_quality" {
  name        = "pec_model_quality_score"
  description = "Mean quality score from MS-014 Evaluator health snapshots"
  filter      = <<-FILTER
    resource.type="cloud_run_revision"
    AND resource.labels.service_name="${var.app_name}-ms-014-evaluator"
    AND jsonPayload.mean_quality!=""
  FILTER

  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "DOUBLE"
    unit        = "1"
    labels {
      key         = "status"
      value_type  = "STRING"
      description = "Model health status"
    }
  }

  value_extractor = "EXTRACT(jsonPayload.mean_quality)"
  label_extractors = {
    "status" = "EXTRACT(jsonPayload.status)"
  }
}

resource "google_monitoring_alert_policy" "model_quality_degraded" {
  display_name = "PEC — AI model quality degraded"
  combiner     = "OR"

  conditions {
    display_name = "Model quality below ${var.quality_alert_threshold}"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.model_quality.name}\""
      comparison      = "COMPARISON_LT"
      threshold_value = var.quality_alert_threshold
      duration        = "600s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  documentation {
    content = <<-DOC
      The PEC Pedagogo model quality has fallen below ${var.quality_alert_threshold}.
      Check MS-014 Evaluator dashboard: ${google_cloud_run_v2_service.ms["ms-014-evaluator"].uri}/api/v1/evaluator/health-report
      Trigger synthetic recovery: POST ${google_cloud_run_v2_service.ms["ms-014-evaluator"].uri}/api/v1/evaluator/synthetic/generate
    DOC
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
  alert_strategy {
    auto_close = "3600s"
  }

  depends_on = [google_logging_metric.model_quality]
}
