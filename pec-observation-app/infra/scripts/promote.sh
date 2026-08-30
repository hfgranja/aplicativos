#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PEC — Promote image tag across environments                                 ║
# ║  Uso: bash infra/scripts/promote.sh --from homol --to preprod --sha <SHA>   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }
hdr()  { echo -e "\n${CYAN}══ $* ══${NC}"; }

FROM_ENV=""
TO_ENV=""
SHA=""

for arg in "$@"; do
  case $arg in
    --from=*)  FROM_ENV="${arg#*=}" ;;
    --from)    shift; FROM_ENV="$1" ;;
    --to=*)    TO_ENV="${arg#*=}" ;;
    --to)      shift; TO_ENV="$1" ;;
    --sha=*)   SHA="${arg#*=}" ;;
    --sha)     shift; SHA="$1" ;;
  esac
done

[[ -z "$FROM_ENV" || -z "$TO_ENV" || -z "$SHA" ]] && \
  err "Uso: promote.sh --from <env> --to <env> --sha <git-sha>"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_DIR="$ROOT/infra/gcp/environments"

FROM_TFVARS="$ENV_DIR/${FROM_ENV}.tfvars"
TO_TFVARS="$ENV_DIR/${TO_ENV}.tfvars"

[[ -f "$FROM_TFVARS" ]] || err "tfvars não encontrado: $FROM_TFVARS"
[[ -f "$TO_TFVARS" ]] || err "tfvars não encontrado: $TO_TFVARS"

FROM_PROJECT=$(grep '^project_id' "$FROM_TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
TO_PROJECT=$(grep '^project_id' "$TO_TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
FROM_APP=$(grep '^app_name' "$FROM_TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
TO_APP=$(grep '^app_name' "$TO_TFVARS" | sed 's/.*= *"\(.*\)"/\1/')
REGION=$(grep '^region' "$FROM_TFVARS" | sed 's/.*= *"\(.*\)"/\1/' || echo "southamerica-east1")

FROM_REGISTRY="$REGION-docker.pkg.dev/$FROM_PROJECT/$FROM_APP"
TO_REGISTRY="$REGION-docker.pkg.dev/$TO_PROJECT/$TO_APP"

hdr "Promote $FROM_ENV → $TO_ENV (SHA=$SHA)"
echo "  De:   $FROM_REGISTRY"
echo "  Para: $TO_REGISTRY"
echo ""

SERVICES=(
  ms-001-identity ms-002-school ms-003-observation
  ms-004-audio-ingestion ms-005-transcription
  ms-006-ai-feedback ms-007-feedback ms-008-pdf-export
  ms-009-audit ms-010-consent ms-011-knowledge
  ms-012-best-practices ms-013-learning ms-014-evaluator
  ms-015-mcp web-app
)

gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

hdr "Re-tagging and pushing images"
PIDS=()
for svc in "${SERVICES[@]}"; do
  (
    SRC_TAG="${FROM_ENV}-${SHA}"
    DST_TAG="${TO_ENV}-${SHA}"
    docker pull "${FROM_REGISTRY}/${svc}:${SRC_TAG}" 2>/dev/null || {
      echo "SKIP: ${svc} — imagem ${SRC_TAG} não encontrada no registry de origem"
      exit 0
    }
    docker tag "${FROM_REGISTRY}/${svc}:${SRC_TAG}" "${TO_REGISTRY}/${svc}:${DST_TAG}"
    docker tag "${FROM_REGISTRY}/${svc}:${SRC_TAG}" "${TO_REGISTRY}/${svc}:${TO_ENV}-latest"
    docker push "${TO_REGISTRY}/${svc}:${DST_TAG}"
    docker push "${TO_REGISTRY}/${svc}:${TO_ENV}-latest"
    echo "  promoted: ${svc}"
  ) &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "Imagens promovidas"

hdr "Deploy Cloud Run ($TO_ENV)"
gcloud config set project "$TO_PROJECT"
PIDS=()
for svc in "${SERVICES[@]}"; do
  gcloud run deploy "${TO_APP}-${svc}" \
    --image="${TO_REGISTRY}/${svc}:${TO_ENV}-${SHA}" \
    --region="$REGION" --project="$TO_PROJECT" --quiet &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "Serviços atualizados em $TO_ENV"
