# ── PEC Observation App — Pré-Produção ───────────────────────────────────────
# GCP Project: pec-obs-stg
# Acesso: tech leads + ops (via IAP em TODOS os endpoints admin)
# Dados: sintéticos de volume (1000+ professores, NUNCA dados reais)
# Espelho de prod com ZONAL (não REGIONAL) para reduzir custo

project_id  = "pec-obs-stg"
region      = "southamerica-east1"
environment = "preprod"
app_name    = "pec-stg"

# ── Banco de dados ────────────────────────────────────────────────────────────
# Mesmo tier de prod para realistic performance testing
db_tier     = "db-custom-2-4096"

# REQUIRED: gere senhas fortes e distintas de prod
# openssl rand -base64 24 | tr -d '/+='
db_password = "FILL_BEFORE_DEPLOY"

# ── JWT ───────────────────────────────────────────────────────────────────────
# REQUIRED: chave distinta de prod
# openssl rand -hex 32
jwt_secret_key = "FILL_BEFORE_DEPLOY"

# ── Ollama VM ─────────────────────────────────────────────────────────────────
ollama_machine_type    = "e2-standard-2"   # 2 vCPU, 8 GB — ~R$275/mês
ollama_model           = "llama3.2"
ollama_embedding_model = "nomic-embed-text"
pec_model_name         = "pec-pedagogo"

# ── Whisper ───────────────────────────────────────────────────────────────────
whisper_model_size = "small"

# ── Cloud Run — escala mínima igual a prod para testar cold-start ──────────────
cloud_run_min_instances = 0
cloud_run_max_instances = 5
cloud_run_cpu           = "1"
cloud_run_memory        = "512Mi"

cloud_run_min_instances_override = {
  "ms-001-identity"    = 1
  "ms-003-observation" = 1
}
cloud_run_max_instances_override = {
  "ms-005-transcription" = 2
  "ms-006-ai-feedback"   = 2
  "ms-013-learning"      = 1
  "ms-014-evaluator"     = 1
}
cloud_run_cpu_override = {
  "ms-005-transcription"  = "4"
  "ms-006-ai-feedback"    = "2"
  "ms-013-learning"       = "2"
  "ms-014-evaluator"      = "2"
  "ms-012-best-practices" = "2"
}
cloud_run_memory_override = {
  "ms-005-transcription"  = "4Gi"
  "ms-006-ai-feedback"    = "1Gi"
  "ms-013-learning"       = "1Gi"
  "ms-014-evaluator"      = "1Gi"
  "ms-012-best-practices" = "2Gi"
}

# ── Monitoring ────────────────────────────────────────────────────────────────
alert_email             = "FILL_BEFORE_DEPLOY"   # e-mail da equipe de ops
quality_alert_threshold = 0.60

# ── LGPD — políticas ativas (dados sintéticos mas pipeline real) ───────────────
audio_retention_days = 7

# ── Segurança ─────────────────────────────────────────────────────────────────
enable_waf           = true    # Cloud Armor com OWASP CRS
enable_iap           = true    # IAP em todos os endpoints admin
enable_cmek          = false   # CMEK somente em prod
enable_binary_auth   = false   # Binary Auth somente em prod

# Membros com acesso admin via IAP
iap_allowed_members = [
  "FILL_BEFORE_DEPLOY",   # ex: "group:ops@pec.seduc.sp.gov.br"
]

allowed_ingress_cidrs = []
