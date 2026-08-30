#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PEC Observation App — Multi-Environment Deploy                              ║
# ║  Uso: bash infra/scripts/deploy-env.sh --env [homol|preprod|prod]           ║
# ║       [--skip-build] [--skip-tf]                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TF_DIR="$ROOT/infra/gcp/terraform"
ENV_DIR="$ROOT/infra/gcp/environments"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }
hdr()  { echo -e "\n${CYAN}══ $* ══${NC}"; }

# ── Argumentos ────────────────────────────────────────────────────────────────
ENV=""
SKIP_BUILD=false
SKIP_TF=false
REQUIRE_APPROVAL=false

for arg in "$@"; do
  case $arg in
    --env=*)       ENV="${arg#*=}" ;;
    --env)         shift; ENV="${1}" ;;
    --skip-build)  SKIP_BUILD=true ;;
    --skip-tf)     SKIP_TF=true ;;
    --require-approval) REQUIRE_APPROVAL=true ;;
  esac
done

[[ -z "$ENV" ]] && err "Ambiente obrigatório: --env [homol|preprod|prod]"
[[ "$ENV" != "homol" && "$ENV" != "preprod" && "$ENV" != "prod" ]] && \
  err "Ambiente inválido: '$ENV'. Use: homol | preprod | prod"

TFVARS_FILE="$ENV_DIR/${ENV}.tfvars"
[[ -f "$TFVARS_FILE" ]] || err "Arquivo não encontrado: $TFVARS_FILE"

# Verificar placeholders não preenchidos
if grep -q "FILL_BEFORE_DEPLOY" "$TFVARS_FILE" 2>/dev/null; then
  err "terraform.tfvars ainda tem placeholders FILL_BEFORE_DEPLOY.\n  Edite: $TFVARS_FILE"
fi

# Extrair variáveis do tfvars
PROJECT_ID=$(grep '^project_id' "$TFVARS_FILE" | sed 's/.*= *"\(.*\)"/\1/')
REGION=$(grep '^region' "$TFVARS_FILE" | sed 's/.*= *"\(.*\)"/\1/' || echo "southamerica-east1")
APP_NAME=$(grep '^app_name' "$TFVARS_FILE" | sed 's/.*= *"\(.*\)"/\1/')
STATE_BUCKET="pec-obs-${ENV}-tf-state"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${APP_NAME}"

hdr "Deploy — Ambiente: $ENV | Projeto: $PROJECT_ID | Região: $REGION"

# ── Aprovação obrigatória para prod ───────────────────────────────────────────
if [[ "$ENV" == "prod" || "$REQUIRE_APPROVAL" == "true" ]]; then
  warn "ATENÇÃO: Deploy em PRODUÇÃO com dados reais de professores SEDUC/SP."
  warn "Este ambiente está em compliance LGPD — qualquer erro pode impactar professores."
  echo ""
  read -r -p "  Digite 'CONFIRMAR PRODUCAO' para prosseguir: " CONFIRM
  [[ "$CONFIRM" != "CONFIRMAR PRODUCAO" ]] && err "Deploy cancelado."
  ok "Aprovação confirmada. Iniciando deploy em produção."
fi

# ── Pre-flight ─────────────────────────────────────────────────────────────────
hdr "Pre-flight checks"

command -v gcloud    &>/dev/null || err "gcloud CLI não encontrado"
command -v docker    &>/dev/null || err "Docker não encontrado"
command -v terraform &>/dev/null || err "Terraform não encontrado"

gcloud config set project "$PROJECT_ID"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
ok "gcloud configurado para projeto $PROJECT_ID"

# ── Terraform ─────────────────────────────────────────────────────────────────
if [[ "$SKIP_TF" == "false" ]]; then
  hdr "Terraform — infraestrutura ($ENV)"

  if ! gsutil ls -b "gs://$STATE_BUCKET" &>/dev/null; then
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$STATE_BUCKET"
    gsutil versioning set on "gs://$STATE_BUCKET"
    ok "State bucket criado: gs://$STATE_BUCKET"
  fi

  cd "$TF_DIR"
  terraform init \
    -backend-config="bucket=$STATE_BUCKET" \
    -backend-config="prefix=pec-observation-app/terraform/state" \
    -reconfigure -input=false

  terraform plan \
    -var-file="$TFVARS_FILE" \
    -out=tfplan \
    -input=false

  # Para preprod/prod, mostrar o plan e pedir confirmação extra
  if [[ "$ENV" == "preprod" || "$ENV" == "prod" ]]; then
    terraform show tfplan
    read -r -p "  Aplicar o plan acima? [yes/N]: " APPLY_CONFIRM
    [[ "$APPLY_CONFIRM" != "yes" ]] && err "Terraform apply cancelado."
  fi

  terraform apply -auto-approve tfplan
  ok "Infraestrutura aplicada"
  cd "$ROOT"
else
  warn "Pulando Terraform (--skip-tf)"
fi

# ── Build Docker ───────────────────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == "false" ]]; then
  hdr "Build Docker images ($ENV)"
  cd "$ROOT"

  SERVICES=(
    ms-001-identity ms-002-school ms-003-observation
    ms-004-audio-ingestion ms-005-transcription
    ms-006-ai-feedback ms-007-feedback ms-008-pdf-export
    ms-009-audit ms-010-consent ms-011-knowledge
    ms-012-best-practices ms-013-learning ms-014-evaluator
    ms-015-mcp
  )

  SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")
  TAG="${ENV}-${SHA}"

  for svc in "${SERVICES[@]}"; do
    echo -n "  Building $svc..."
    docker build \
      -t "${REGISTRY}/${svc}:${TAG}" \
      -t "${REGISTRY}/${svc}:${ENV}-latest" \
      -f "services/${svc}/Dockerfile" \
      . &>/tmp/build-${svc}.log && ok "$svc" || {
        warn "$svc FAILED — veja /tmp/build-${svc}.log"
      }
  done

  echo -n "  Building web-app..."
  docker build \
    -t "${REGISTRY}/web-app:${TAG}" \
    -t "${REGISTRY}/web-app:${ENV}-latest" \
    web-app &>/tmp/build-web-app.log && ok "web-app" || warn "web-app FAILED"

  ok "Images construídas (TAG=$TAG)"
  cd "$ROOT"
else
  warn "Pulando Docker build (--skip-build)"
  TAG="${ENV}-latest"
fi

# ── Push ──────────────────────────────────────────────────────────────────────
hdr "Push images → Artifact Registry ($PROJECT_ID)"

PIDS=()
for svc in ms-001-identity ms-002-school ms-003-observation \
           ms-004-audio-ingestion ms-005-transcription \
           ms-006-ai-feedback ms-007-feedback ms-008-pdf-export \
           ms-009-audit ms-010-consent ms-011-knowledge \
           ms-012-best-practices ms-013-learning ms-014-evaluator \
           ms-015-mcp web-app; do
  docker push "${REGISTRY}/${svc}:${ENV}-latest" &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "Todas as images enviadas"

# ── Deploy Cloud Run ───────────────────────────────────────────────────────────
hdr "Deploy Cloud Run ($REGION)"

PIDS=()
for svc in ms-001-identity ms-002-school ms-003-observation \
           ms-004-audio-ingestion ms-005-transcription \
           ms-006-ai-feedback ms-007-feedback ms-008-pdf-export \
           ms-009-audit ms-010-consent ms-011-knowledge \
           ms-012-best-practices ms-013-learning ms-014-evaluator \
           ms-015-mcp; do
  gcloud run deploy "${APP_NAME}-${svc}" \
    --image "${REGISTRY}/${svc}:${ENV}-latest" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --quiet &
  PIDS+=($!)
done
gcloud run deploy "${APP_NAME}-web-app" \
  --image "${REGISTRY}/web-app:${ENV}-latest" \
  --region "$REGION" --project "$PROJECT_ID" --quiet &
PIDS+=($!)
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "Todos os serviços deployados"

# ── URLs ──────────────────────────────────────────────────────────────────────
hdr "URLs do ambiente $ENV"

WEB_URL=$(gcloud run services describe "${APP_NAME}-web-app" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")
IDENTITY_URL=$(gcloud run services describe "${APP_NAME}-ms-001-identity" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")
MCP_URL=$(gcloud run services describe "${APP_NAME}-ms-015-mcp" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")

echo ""
echo "  Ambiente:      $ENV"
echo "  Projeto GCP:   $PROJECT_ID"
echo "  SHA:           $TAG"
echo "  Web App:       $WEB_URL"
echo "  Identity:      $IDENTITY_URL"
echo "  MCP:           $MCP_URL/mcp"
echo ""

# ── Smoke test ────────────────────────────────────────────────────────────────
hdr "Smoke test"

if [[ "$IDENTITY_URL" != "N/A" ]]; then
  curl -sf "${IDENTITY_URL}/health" &>/dev/null && ok "Identity service OK" || warn "Identity não respondeu ainda"
fi
if [[ "$WEB_URL" != "N/A" ]]; then
  curl -sf "${WEB_URL}/" &>/dev/null && ok "Web app OK" || warn "Web app não respondeu ainda (aguarde 30s)"
fi

echo ""
ok "Deploy em $ENV concluído!"
echo "  Monitoramento: https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"
