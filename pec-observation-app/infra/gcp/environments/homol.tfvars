# ── PEC Observation App — Homologação ────────────────────────────────────────
# GCP Project: pec-obs-hom
# Acesso: devs + QA + product (via IAP nos endpoints admin)
# Dados: sintéticos apenas — NUNCA dados reais de professores

project_id  = "pec-obs-hom"
region      = "southamerica-east1"
environment = "homologacao"
app_name    = "pec-hom"

# ── Banco de dados ────────────────────────────────────────────────────────────
# db-g1-small: 1 vCPU shared, 614MB RAM — suficiente para testes (~$10/mês)
db_tier     = "db-g1-small"

# REQUIRED: preencher antes de executar terraform apply
# openssl rand -base64 24 | tr -d '/+='
db_password = "FILL_BEFORE_DEPLOY"

# ── JWT ───────────────────────────────────────────────────────────────────────
# openssl rand -hex 32
jwt_secret_key = "FILL_BEFORE_DEPLOY"

# ── Ollama VM (menor — apenas para testes funcionais) ─────────────────────────
ollama_machine_type    = "e2-medium"       # 2 vCPU, 4 GB — ~R$150/mês
ollama_model           = "llama3.2"
ollama_embedding_model = "nomic-embed-text"
pec_model_name         = "pec-pedagogo"

# ── Whisper (mais rápido para homol) ──────────────────────────────────────────
whisper_model_size = "tiny"

# ── Cloud Run — tudo scale-to-zero para economizar ───────────────────────────
cloud_run_min_instances = 0
cloud_run_max_instances = 2
cloud_run_cpu           = "1"
cloud_run_memory        = "512Mi"

# Sem overrides — tudo vai para zero quando inativo
cloud_run_min_instances_override = {}
cloud_run_max_instances_override = {}
cloud_run_cpu_override           = {}
cloud_run_memory_override        = {}

# ── Monitoring ────────────────────────────────────────────────────────────────
alert_email             = "FILL_BEFORE_DEPLOY"   # e-mail da equipe de dev/QA
quality_alert_threshold = 0.50                    # limiar menor para homol

# ── LGPD — retenção reduzida (dados sintéticos) ───────────────────────────────
audio_retention_days = 1

# ── Segurança ─────────────────────────────────────────────────────────────────
enable_waf           = false   # Cloud Armor não necessário em homol
enable_iap           = true    # IAP nos endpoints admin
enable_cmek          = false   # CMEK somente em prod
enable_binary_auth   = false   # Binary Auth somente em prod

# Membros com acesso aos endpoints admin via IAP
# Formato: "user:email@example.com" | "group:grp@example.com"
iap_allowed_members = [
  "FILL_BEFORE_DEPLOY",   # ex: "group:devs@pec.seduc.sp.gov.br"
]

# IPs permitidos para acessar o ambiente (CIDR notation)
# Deixar vazio para permitir todos (menos recomendado)
allowed_ingress_cidrs = []
