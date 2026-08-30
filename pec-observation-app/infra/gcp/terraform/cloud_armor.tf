# ── Cloud Armor WAF ───────────────────────────────────────────────────────────
# Habilitado em: preprod (OWASP CRS apenas) e prod (OWASP CRS + custom rules)
# DEV e HOMOL: desabilitado (enable_waf = false)
#
# ATENÇÃO: Cloud Armor requer um Global HTTPS Load Balancer.
# Para Cloud Run direto, o backend service é configurado via NEG serverless.

# Serverless NEG para o API gateway (Cloud Run web-app que faz proxy para MSs)
resource "google_compute_region_network_endpoint_group" "web_app_neg" {
  count = var.enable_waf ? 1 : 0

  name                  = "${var.app_name}-web-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.web_app.name
  }
}

# Backend service (conecta o LB ao Cloud Run via NEG)
resource "google_compute_backend_service" "web_app" {
  count = var.enable_waf ? 1 : 0

  name                  = "${var.app_name}-backend"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  security_policy       = google_compute_security_policy.api_waf[0].id

  backend {
    group = google_compute_region_network_endpoint_group.web_app_neg[0].id
  }
}

# Cloud Armor Security Policy
resource "google_compute_security_policy" "api_waf" {
  count = var.enable_waf ? 1 : 0

  name        = "${var.app_name}-waf"
  description = "WAF policy for PEC ${var.environment} — OWASP CRS + rate limiting"

  # ── OWASP Core Rule Set (CRS) ─────────────────────────────────────────────
  rule {
    action   = "deny(403)"
    priority = 1000
    match {
      expr {
        # SQLi — SQL Injection
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block SQL injection"
  }

  rule {
    action   = "deny(403)"
    priority = 1001
    match {
      expr {
        # XSS — Cross-Site Scripting
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block XSS"
  }

  rule {
    action   = "deny(403)"
    priority = 1002
    match {
      expr {
        # LFI — Local File Inclusion
        expression = "evaluatePreconfiguredExpr('lfi-v33-stable')"
      }
    }
    description = "Block LFI"
  }

  rule {
    action   = "deny(403)"
    priority = 1003
    match {
      expr {
        # RFI — Remote File Inclusion
        expression = "evaluatePreconfiguredExpr('rfi-v33-stable')"
      }
    }
    description = "Block RFI"
  }

  rule {
    action   = "deny(403)"
    priority = 1004
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rce-v33-stable')"
      }
    }
    description = "Block Remote Code Execution"
  }

  # ── Rate limiting global ──────────────────────────────────────────────────
  rule {
    action   = "throttle"
    priority = 2000
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      rate_limit_threshold {
        count        = 1000
        interval_sec = 60
      }
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
    }
    description = "Global rate limit: 1000 req/min per IP"
  }

  # ── Rate limiting para auth (anti-brute-force) ────────────────────────────
  rule {
    action   = "throttle"
    priority = 2001
    match {
      expr {
        expression = "request.path.matches('/api/v1/auth/.*')"
      }
    }
    rate_limit_options {
      rate_limit_threshold {
        count        = 10
        interval_sec = 60
      }
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
    }
    description = "Auth rate limit: 10 req/min per IP (anti-brute-force)"
  }

  # ── Regras adicionais para produção ───────────────────────────────────────
  dynamic "rule" {
    for_each = var.environment == "production" ? [1] : []
    content {
      action   = "deny(403)"
      priority = 3000
      match {
        expr {
          # Scanner fingerprinting — bloquear ferramentas comuns de scan
          expression = "evaluatePreconfiguredExpr('scannerdetection-v33-stable')"
        }
      }
      description = "Block scanner tools (prod only)"
    }
  }

  # ── Default: permitir ─────────────────────────────────────────────────────
  rule {
    action   = "allow"
    priority = 2147483647
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default: allow"
  }
}
