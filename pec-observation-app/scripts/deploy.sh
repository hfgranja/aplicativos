#!/usr/bin/env bash
# PEC Observation App — Full Production Deploy Script
# Usage: bash scripts/deploy.sh [--skip-build]
#
# What it does:
#   1. Validates .env.production exists and has no placeholder values
#   2. Pulls latest base images
#   3. Builds all production Docker images (unless --skip-build)
#   4. Rolls out services with zero-downtime strategy
#   5. Waits for all health checks to pass
#   6. Prints service status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE="docker compose -f $ROOT/docker-compose.prod.yml --env-file $ROOT/.env.production"
SKIP_BUILD=false

# ── Parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --skip-build) SKIP_BUILD=true ;;
    *) echo "Unknown argument: $arg"; exit 1 ;;
  esac
done

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

# ── 1. Validate env file ──────────────────────────────────────────────────────
echo "→ Validating .env.production..."
[[ -f "$ROOT/.env.production" ]] || err ".env.production not found. Copy and fill it first."

for placeholder in "CHANGE_ME" "YOUR_"; do
  if grep -q "$placeholder" "$ROOT/.env.production"; then
    err ".env.production still has placeholder values ($placeholder). Fill all secrets before deploying."
  fi
done
ok ".env.production validated"

# ── 2. Pull base images ───────────────────────────────────────────────────────
echo "→ Pulling latest base images..."
docker pull python:3.12-slim  --quiet
docker pull node:20-alpine    --quiet
docker pull postgres:16-alpine --quiet
docker pull redis:7-alpine    --quiet
docker pull minio/minio:latest --quiet
docker pull nginx:1.27-alpine  --quiet
ok "Base images updated"

# ── 3. Build production images ────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == "false" ]]; then
  echo "→ Building production images (this may take ~10 minutes first time)..."
  $COMPOSE build --parallel --quiet
  ok "Images built"
else
  warn "Skipping build (--skip-build flag)"
fi

# ── 4. Start / update infra first ─────────────────────────────────────────────
echo "→ Starting infrastructure services..."
$COMPOSE up -d postgres redis minio
echo "  Waiting for Postgres..."
until $COMPOSE exec -T postgres pg_isready -q 2>/dev/null; do sleep 2; done
echo "  Waiting for Redis..."
until $COMPOSE exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; do sleep 2; done
echo "  Waiting for MinIO..."
until $COMPOSE exec -T minio curl -sf http://localhost:9000/minio/health/live 2>/dev/null; do sleep 3; done
ok "Infrastructure healthy"

# ── 5. Initialise MinIO buckets ───────────────────────────────────────────────
echo "→ Initialising MinIO buckets..."
$COMPOSE up minio-init
ok "Buckets ready"

# ── 6. Start microservices ────────────────────────────────────────────────────
SERVICES=(
  ms-001-identity ms-002-school ms-003-observation
  ms-004-audio-ingestion ms-005-transcription
  ms-006-ai-feedback ms-007-feedback ms-008-pdf-export
  ms-009-audit ms-010-consent ms-011-knowledge ms-012-best-practices
)

echo "→ Starting microservices..."
$COMPOSE up -d "${SERVICES[@]}"

# ── 7. Wait for all microservices to be healthy ───────────────────────────────
echo "→ Waiting for microservices to become healthy (max 3 min)..."
DEADLINE=$(( $(date +%s) + 180 ))
for svc in "${SERVICES[@]}"; do
  echo -n "  $svc "
  while true; do
    STATUS=$($COMPOSE ps "$svc" --format json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health',''))" 2>/dev/null || echo "")
    if [[ "$STATUS" == "healthy" ]]; then
      echo -e "${GREEN}healthy${NC}"; break
    fi
    if [[ $(date +%s) -gt $DEADLINE ]]; then
      echo -e "${RED}timeout${NC}"
      err "Service $svc did not become healthy in time. Check logs: docker compose logs $svc"
    fi
    echo -n "."
    sleep 5
  done
done
ok "All microservices healthy"

# ── 8. Start API gateway ──────────────────────────────────────────────────────
echo "→ Starting API gateway..."
$COMPOSE up -d api-gateway
sleep 3
if ! $COMPOSE exec -T api-gateway wget -qO- http://localhost/health 2>/dev/null; then
  warn "Gateway health check pending — it may still be starting"
fi
ok "API gateway started"

# ── 9. Final status ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════"
$COMPOSE ps --format "table {{.Service}}\t{{.Status}}\t{{.Ports}}"
echo "════════════════════════════════════════════"
HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo ""
ok "Deploy complete!"
echo "  → Web app:  http://${HOST_IP}"
echo "  → Health:   http://${HOST_IP}/health"
