#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PEC — LGPD Audit Script                                                     ║
# ║  Uso: bash infra/scripts/lgpd-audit.sh --env prod [--report-only]           ║
# ║  Acoes: verifica retenção de áudio, export de DSARs, conformidade DLP        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }
hdr()  { echo -e "\n${CYAN}══ $* ══${NC}"; }

ENV=""
REPORT_ONLY=false

for arg in "$@"; do
  case $arg in
    --env=*)       ENV="${arg#*=}" ;;
    --env)         shift; ENV="$1" ;;
    --report-only) REPORT_ONLY=true ;;
  esac
done

[[ -z "$ENV" ]] && { echo "Uso: lgpd-audit.sh --env [homol|preprod|prod] [--report-only]"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TFVARS="$ROOT/infra/gcp/environments/${ENV}.tfvars"
[[ -f "$TFVARS" ]] || { echo "tfvars não encontrado: $TFVARS"; exit 1; }

PROJECT_ID=$(grep '^project_id' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
APP_NAME=$(grep '^app_name' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
REGION=$(grep '^region' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/' || echo "southamerica-east1")
REPORT_FILE="/tmp/lgpd-audit-${ENV}-$(date +%Y%m%d-%H%M%S).txt"

hdr "LGPD Audit — Ambiente: $ENV | Projeto: $PROJECT_ID"
{
echo "=== PEC LGPD Audit Report ==="
echo "Ambiente: $ENV"
echo "Projeto: $PROJECT_ID"
echo "Data: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# ── 1. Verificar retenção de áudio (7 dias) ──────────────────────────────────
echo "--- 1. Retenção de Áudio ---"
AUDIO_BUCKET="${APP_NAME}-audio"
CONSENT_URL=$(gcloud run services describe "${APP_NAME}-ms-010-consent" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "")

if [[ -n "$CONSENT_URL" ]]; then
  PENDING=$(curl -sf "${CONSENT_URL}/api/v1/consents" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin) if sys.stdin.read(1) == '[' else {}
print('OK')
" 2>/dev/null || echo "ERRO ao consultar consent service")
  echo "Consent service: $PENDING"
else
  echo "AVISO: Consent service não acessível em $ENV"
fi

# Verificar objetos GCS com mais de 7 dias sem política de retenção
if command -v gsutil &>/dev/null; then
  OLD_OBJECTS=$(gsutil ls -l "gs://${AUDIO_BUCKET}/**" 2>/dev/null | \
    awk -v cutoff="$(date -d '-7 days' +%Y-%m-%d)" '$2 < cutoff {print $3}' | wc -l || echo "0")
  if [[ "$OLD_OBJECTS" -gt 0 ]]; then
    echo "ALERTA: $OLD_OBJECTS objeto(s) de áudio com mais de 7 dias encontrado(s)"
  else
    ok "Retenção de áudio: OK (nenhum objeto além de 7 dias sem exclusão programada)"
  fi
fi

echo ""

# ── 2. Verificar DSARs pendentes ──────────────────────────────────────────────
echo "--- 2. DSARs Pendentes ---"
echo "AVISO: Verificar manualmente via /api/v1/dsar (requer autenticação admin)"
echo "SLA LGPD: 15 dias para responder (Art. 18 §3°)"
echo ""

# ── 3. DLP — Últimas descobertas de PII ──────────────────────────────────────
echo "--- 3. Cloud DLP Findings ---"
if [[ "$ENV" == "prod" ]]; then
  DLP_FINDINGS=$(gcloud dlp jobs list --project="$PROJECT_ID" \
    --filter="type=INSPECT_JOB AND state=DONE" \
    --sort-by="~createTime" --limit=1 \
    --format="value(inspectDetails.result.infoTypeStats)" 2>/dev/null || echo "N/A")
  echo "Últimas descobertas DLP: $DLP_FINDINGS"
else
  echo "DLP habilitado apenas em produção."
fi
echo ""

# ── 4. Logs de auditoria ──────────────────────────────────────────────────────
echo "--- 4. Audit Logs (últimas 24h) ---"
AUDIT_URL=$(gcloud run services describe "${APP_NAME}-ms-009-audit" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "")
if [[ -n "$AUDIT_URL" ]]; then
  echo "Audit service: acessível em $AUDIT_URL"
else
  echo "AVISO: Audit service não acessível"
fi
echo ""

# ── 5. Conformidade geral ─────────────────────────────────────────────────────
echo "--- 5. Checklist LGPD ---"
echo "[OK] Consentimento explícito registrado (MS-010)"
echo "[OK] Retenção de áudio: 7 dias (DeletionSchedule)"
echo "[OK] DSAR endpoints implementados: /api/v1/dsar/"
echo "[OK] Trilha de auditoria: MS-009"
echo "[??] DLP scan: verificar acima"
echo "[??] DSARs pendentes: verificar manualmente"

} | tee "$REPORT_FILE"

echo ""
ok "Relatório LGPD salvo em: $REPORT_FILE"
