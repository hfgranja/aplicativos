#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  PEC Observation App — Google Cloud Deploy Script                           ║
# ║  Projeto: feedback-automatico-pec                                           ║
# ║  Conta:   henriquef.granja@gmail.com                                        ║
# ║                                                                              ║
# ║  Uso:  bash infra/scripts/deploy-gcp.sh [--skip-build] [--skip-tf]         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TF_DIR="$ROOT/infra/gcp/terraform"

PROJECT_ID="feedback-automatico-pec"
REGION="southamerica-east1"
APP_NAME="pec-obs"
STATE_BUCKET="pec-obs-terraform-state"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/pec-obs"

SKIP_BUILD=false
SKIP_TF=false
for arg in "$@"; do
  case $arg in
    --skip-build) SKIP_BUILD=true ;;
    --skip-tf)    SKIP_TF=true ;;
  esac
done

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }
hdr()  { echo -e "\n${CYAN}══ $* ══${NC}"; }

# ── 0. Pre-flight ─────────────────────────────────────────────────────────────
hdr "Pre-flight checks"

command -v gcloud    &>/dev/null || err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
command -v docker    &>/dev/null || err "Docker not found"
command -v terraform &>/dev/null || err "Terraform not found. Install: https://developer.hashicorp.com/terraform/install"

gcloud config set project "$PROJECT_ID"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
ok "gcloud configured for project $PROJECT_ID"

# Check terraform.tfvars has no placeholder values
if grep -q "FILL_BEFORE_DEPLOY" "$TF_DIR/terraform.tfvars" 2>/dev/null; then
  err "terraform.tfvars still has FILL_BEFORE_DEPLOY placeholders.\n  Edit: $TF_DIR/terraform.tfvars"
fi

# ── 1. Terraform infrastructure ───────────────────────────────────────────────
if [[ "$SKIP_TF" == "false" ]]; then
  hdr "Terraform — infrastructure"

  # Create state bucket if it doesn't exist
  if ! gsutil ls -b "gs://$STATE_BUCKET" &>/dev/null; then
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$STATE_BUCKET"
    gsutil versioning set on "gs://$STATE_BUCKET"
    ok "State bucket created: gs://$STATE_BUCKET"
  fi

  cd "$TF_DIR"
  terraform init -backend-config="bucket=$STATE_BUCKET" -reconfigure -input=false
  terraform plan -out=tfplan -input=false
  terraform apply -auto-approve tfplan
  ok "Infrastructure applied"
  cd "$ROOT"
else
  warn "Skipping Terraform (--skip-tf)"
fi

# ── 2. Build Docker images ────────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == "false" ]]; then
  hdr "Building Docker images"
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

  for svc in "${SERVICES[@]}"; do
    echo -n "  Building $svc..."
    docker build \
      -t "${REGISTRY}/${svc}:${SHA}" \
      -t "${REGISTRY}/${svc}:latest" \
      -f "services/${svc}/Dockerfile" \
      . &>/tmp/build-${svc}.log && ok "$svc" || {
        warn "$svc FAILED — check /tmp/build-${svc}.log"
      }
  done

  echo -n "  Building web-app..."
  docker build \
    -t "${REGISTRY}/web-app:${SHA}" \
    -t "${REGISTRY}/web-app:latest" \
    web-app &>/tmp/build-web-app.log && ok "web-app" || warn "web-app FAILED"

  ok "All images built (SHA=$SHA)"
  cd "$ROOT"
else
  warn "Skipping Docker build (--skip-build)"
  SHA="latest"
fi

# ── 3. Push images ────────────────────────────────────────────────────────────
hdr "Pushing images to Artifact Registry"

PIDS=()
for svc in ms-001-identity ms-002-school ms-003-observation \
           ms-004-audio-ingestion ms-005-transcription \
           ms-006-ai-feedback ms-007-feedback ms-008-pdf-export \
           ms-009-audit ms-010-consent ms-011-knowledge \
           ms-012-best-practices ms-013-learning ms-014-evaluator \
           ms-015-mcp web-app; do
  docker push "${REGISTRY}/${svc}:latest" &
  PIDS+=($!)
done
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "All images pushed"

# ── 4. Deploy to Cloud Run ────────────────────────────────────────────────────
hdr "Deploying to Cloud Run ($REGION)"

PIDS=()
for svc in ms-001-identity ms-002-school ms-003-observation \
           ms-004-audio-ingestion ms-005-transcription \
           ms-006-ai-feedback ms-007-feedback ms-008-pdf-export \
           ms-009-audit ms-010-consent ms-011-knowledge \
           ms-012-best-practices ms-013-learning ms-014-evaluator \
           ms-015-mcp; do
  gcloud run deploy "${APP_NAME}-${svc}" \
    --image "${REGISTRY}/${svc}:latest" \
    --region "$REGION" \
    --project "$PROJECT_ID" \
    --quiet &
  PIDS+=($!)
done
gcloud run deploy "${APP_NAME}-web-app" \
  --image "${REGISTRY}/web-app:latest" \
  --region "$REGION" --project "$PROJECT_ID" --quiet &
PIDS+=($!)
for pid in "${PIDS[@]}"; do wait "$pid"; done
ok "All services deployed"

# ── 5. Print URLs ─────────────────────────────────────────────────────────────
hdr "Service URLs"

WEB_URL=$(gcloud run services describe "${APP_NAME}-web-app" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")
IDENTITY_URL=$(gcloud run services describe "${APP_NAME}-ms-001-identity" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")
EVALUATOR_URL=$(gcloud run services describe "${APP_NAME}-ms-014-evaluator" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")
MCP_URL=$(gcloud run services describe "${APP_NAME}-ms-015-mcp" \
  --region="$REGION" --project="$PROJECT_ID" --format="value(status.url)" 2>/dev/null || echo "N/A")

echo ""
echo "  ┌────────────────────────────────────────────────────────────────────┐"
echo "  │  🌐  Web App:          $WEB_URL"
echo "  │  🔐  Identity API:     $IDENTITY_URL"
echo "  │  📊  Model Evaluator:  $EVALUATOR_URL/api/v1/evaluator/health-report"
echo "  │  🔌  MCP Server:       $MCP_URL/mcp"
echo "  └────────────────────────────────────────────────────────────────────┘"
echo ""

# ── 6. Smoke test ─────────────────────────────────────────────────────────────
hdr "Smoke test"

if [[ "$IDENTITY_URL" != "N/A" ]]; then
  curl -sf "${IDENTITY_URL}/health" &>/dev/null && ok "Identity service healthy" || warn "Identity service not responding yet"
fi
if [[ "$WEB_URL" != "N/A" ]]; then
  curl -sf "${WEB_URL}/" &>/dev/null && ok "Web app responding" || warn "Web app not responding yet (may take 30s)"
fi

echo ""
ok "Deploy complete!"
echo "  Monitore alertas em: https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"
