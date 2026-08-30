#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PEC — Rollback Cloud Run services to previous revision                      ║
# ║  Uso: bash infra/scripts/rollback.sh --env [homol|preprod|prod]             ║
# ║       [--service ms-001-identity]  (vazio = todos)                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }
hdr()  { echo -e "\n${CYAN}══ $* ══${NC}"; }

ENV=""
TARGET_SVC=""

for arg in "$@"; do
  case $arg in
    --env=*)      ENV="${arg#*=}" ;;
    --env)        shift; ENV="$1" ;;
    --service=*)  TARGET_SVC="${arg#*=}" ;;
    --service)    shift; TARGET_SVC="$1" ;;
  esac
done

[[ -z "$ENV" ]] && err "Ambiente obrigatório: --env [homol|preprod|prod]"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TFVARS="$ROOT/infra/gcp/environments/${ENV}.tfvars"
[[ -f "$TFVARS" ]] || err "tfvars não encontrado: $TFVARS"

PROJECT_ID=$(grep '^project_id' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
APP_NAME=$(grep '^app_name' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
REGION=$(grep '^region' "$TFVARS" | sed 's/.*= *"\(.*\)"/\1/' || echo "southamerica-east1")

if [[ "$ENV" == "prod" ]]; then
  warn "ATENÇÃO: Rollback em PRODUÇÃO."
  read -r -p "  Digite 'ROLLBACK PRODUCAO' para confirmar: " CONFIRM
  [[ "$CONFIRM" != "ROLLBACK PRODUCAO" ]] && err "Rollback cancelado."
fi

hdr "Rollback — $ENV | Projeto: $PROJECT_ID"

ALL_SERVICES=(
  ms-001-identity ms-002-school ms-003-observation
  ms-004-audio-ingestion ms-005-transcription
  ms-006-ai-feedback ms-007-feedback ms-008-pdf-export
  ms-009-audit ms-010-consent ms-011-knowledge
  ms-012-best-practices ms-013-learning ms-014-evaluator
  ms-015-mcp web-app
)

if [[ -n "$TARGET_SVC" ]]; then
  SERVICES=("$TARGET_SVC")
else
  SERVICES=("${ALL_SERVICES[@]}")
fi

gcloud config set project "$PROJECT_ID"

PIDS=()
for svc in "${SERVICES[@]}"; do
  (
    FULL_NAME="${APP_NAME}-${svc}"
    PREV_REV=$(gcloud run revisions list \
      --service="$FULL_NAME" --region="$REGION" --project="$PROJECT_ID" \
      --format="value(metadata.name)" --sort-by="~metadata.creationTimestamp" \
      --limit=2 2>/dev/null | tail -1)
    if [[ -z "$PREV_REV" ]]; then
      warn "$svc — nenhuma revisão anterior encontrada, ignorando"
      exit 0
    fi
    gcloud run services update-traffic "$FULL_NAME" \
      --to-revisions="${PREV_REV}=100" \
      --region="$REGION" --project="$PROJECT_ID" --quiet
    ok "Rollback ${svc} → ${PREV_REV}"
  ) &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid"; done

hdr "Smoke test pós-rollback"
IDENTITY_URL=$(gcloud run services describe "${APP_NAME}-ms-001-identity" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "")
if [[ -n "$IDENTITY_URL" ]]; then
  curl -sf "${IDENTITY_URL}/health" && ok "Identity OK" || warn "Identity não respondeu"
fi

ok "Rollback em $ENV concluído. Verifique os logs: https://console.cloud.google.com/run?project=$PROJECT_ID"
