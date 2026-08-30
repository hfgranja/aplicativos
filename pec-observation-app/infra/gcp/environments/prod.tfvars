# ── PEC Observation App — Produção ───────────────────────────────────────────
# GCP Project: feedback-automatico-pec (existente)
# Acesso: equipe de ops APENAS — MFA obrigatório no console GCP
# Dados: REAIS — dados pessoais de professores SEDUC/SP
# Conformidade: LGPD + políticas SEDUC

project_id  = "feedback-automatico-pec"
region      = "southamerica-east1"
environment = "production"
app_name    = "pec-obs"

# ── Banco de dados ────────────────────────────────────────────────────────────
# REGIONAL para alta disponibilidade
db_tier     = "db-custom-2-4096"

# REQUIRED: senha forte única — NÃO reutilizar de outros ambientes
# openssl rand -base64 24 | tr -d '/+='
db_password = "FILL_BEFORE_DEPLOY"

# ── JWT ───────────────────────────────────────────────────────────────────────
# REQUIRED: chave única de 64 chars mínimo em prod
# openssl rand -hex 32
jwt_secret_key = "FILL_BEFORE_DEPLOY"

# ── Ollama VM ─────────────────────────────────────────────────────────────────
ollama_machine_type    = "e2-standard-4"   # 4 vCPU, 16 GB — ~R$550/mês
ollama_model           = "llama3.2"
ollama_embedding_model = "nomic-embed-text"
pec_model_name         = "pec-pedagogo"

# ── Whisper ───────────────────────────────────────────────────────────────────
whisper_model_size = "small"

# ── Cloud Run ─────────────────────────────────────────────────────────────────
cloud_run_min_instances = 0
cloud_run_max_instances = 10
cloud_run_cpu           = "1"
cloud_run_memory        = "512Mi"

cloud_run_min_instances_override = {
  "ms-001-identity"    = 1
  "ms-003-observation" = 1
}
cloud_run_max_instances_override = {
  "ms-005-transcription" = 3
  "ms-006-ai-feedback"   = 2
  "ms-013-learning"      = 2
  "ms-014-evaluator"     = 2
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
alert_email             = "henriquef.granja@gmail.com"
quality_alert_threshold = 0.60

# ── LGPD ─────────────────────────────────────────────────────────────────────
audio_retention_days = 7

# ── Segurança PRODUÇÃO ────────────────────────────────────────────────────────
enable_waf           = true    # Cloud Armor full (OWASP CRS + custom rules)
enable_iap           = true    # IAP em todos os endpoints admin
enable_cmek          = true    # CMEK (KMS) para Cloud SQL + GCS áudio
enable_binary_auth   = true    # Apenas imagens assinadas pela Cloud Build SA

# Membros com acesso admin via IAP (somente ops)
iap_allowed_members = [
  "FILL_BEFORE_DEPLOY",   # ex: "group:ops@pec.seduc.sp.gov.br"
]

allowed_ingress_cidrs = []
