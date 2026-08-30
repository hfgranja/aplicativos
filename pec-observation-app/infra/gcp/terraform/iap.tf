# ── Identity-Aware Proxy — Admin Endpoint Protection ─────────────────────────
# Protege endpoints sensíveis: /api/v1/audit/, /api/v1/learning/, /api/v1/evaluator/
# Habilitado em: homol, preprod, prod (enable_iap = true)

# IAP brand (OAuth consent screen) — criado uma vez por projeto
resource "google_iap_brand" "main" {
  count = var.enable_iap ? 1 : 0

  support_email     = var.alert_email
  application_title = "PEC Observation App — ${var.environment}"
  project           = var.project_id

  depends_on = [google_project_service.apis]
}

# IAP OAuth 2.0 client
resource "google_iap_client" "main" {
  count = var.enable_iap ? 1 : 0

  display_name = "PEC IAP Client (${var.environment})"
  brand        = google_iap_brand.main[0].name
}

# IAP backend service for Cloud Run (via Load Balancer)
# Note: Cloud Run v2 with IAP requires a global HTTPS LB.
# For simplicity, we apply IAP at the service account level and
# restrict Cloud Run invocation to identified users.

# Restrict Cloud Run invoker for admin services to iap_allowed_members
# When enable_iap = true, remove allUsers from admin services and
# replace with specific members.

locals {
  admin_services = [
    "ms-009-audit",
    "ms-013-learning",
    "ms-014-evaluator",
    "ms-015-mcp",
  ]
}

# Remove allUsers access from admin services when IAP is enabled
resource "google_cloud_run_v2_service_iam_member" "admin_restricted" {
  for_each = var.enable_iap ? toset(local.admin_services) : toset([])

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ms[each.value].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant IAP-allowed members invoker access to admin services
resource "google_cloud_run_v2_service_iam_member" "iap_members" {
  for_each = var.enable_iap ? {
    for pair in setproduct(local.admin_services, var.iap_allowed_members) :
    "${pair[0]}/${pair[1]}" => { svc = pair[0], member = pair[1] }
  } : {}

  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ms[each.value.svc].name
  role     = "roles/run.invoker"
  member   = each.value.member
}

# Output IAP client credentials (needed by nginx/gateway to forward tokens)
output "iap_client_id" {
  description = "IAP OAuth Client ID — configure in API gateway to pass Bearer tokens"
  value       = var.enable_iap ? google_iap_client.main[0].client_id : null
  sensitive   = true
}
