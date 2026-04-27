#!/usr/bin/env bash
# PEC Observation App — Health Check Script
# Usage: bash scripts/health-check.sh [BASE_URL]
#   BASE_URL defaults to http://localhost
#
# Checks:
#   • API gateway /health
#   • All 12 microservice /health endpoints via the gateway
#   • Postgres connectivity (optional, if running locally)
#   • Redis connectivity (optional)

set -uo pipefail

BASE="${1:-http://localhost}"
TIMEOUT=5

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; GRAY='\033[0;37m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; FAILED=$((FAILED+1)); }
skip() { echo -e "  ${GRAY}–${NC} $* (skipped)"; }

FAILED=0

check_http() {
  local label="$1"
  local url="$2"
  local response
  response=$(curl -sf --max-time "$TIMEOUT" "$url" 2>/dev/null) && \
    pass "$label → $(echo "$response" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("status","ok"))' 2>/dev/null || echo 'ok')" || \
    fail "$label ($url)"
}

echo ""
echo "PEC Observation App — Health Check"
echo "Base URL: ${BASE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Gateway
echo ""
echo "API Gateway"
check_http "gateway" "${BASE}/health"

# Microservices (all routed through gateway by checking internal ports directly
# when running locally, or via the gateway health proxy)
echo ""
echo "Microservices (via gateway or direct)"

# Try direct ports first (dev), fall back to gateway-routed paths
check_ms() {
  local label="$1"; local port="$2"; local gw_path="$3"
  # Try direct port
  if curl -sf --max-time 2 "http://localhost:${port}/health" &>/dev/null; then
    check_http "$label (port $port)" "http://localhost:${port}/health"
  else
    check_http "$label (gateway)" "${BASE}${gw_path}"
  fi
}

check_ms "ms-001 identity"       8001 "/api/v1/auth/health"      2>/dev/null || check_http "ms-001 identity"       "http://localhost:8001/health"
check_ms "ms-002 school"         8002 "/api/v1/schools/health"   2>/dev/null || check_http "ms-002 school"         "http://localhost:8002/health"
check_ms "ms-003 observation"    8003 "/api/v1/observations/health" 2>/dev/null || check_http "ms-003 observation" "http://localhost:8003/health"
check_ms "ms-004 audio"          8004 "/api/v1/audio/health"     2>/dev/null || check_http "ms-004 audio"          "http://localhost:8004/health"
check_ms "ms-005 transcription"  8005 "/api/v1/transcriptions/health" 2>/dev/null || check_http "ms-005 transcription" "http://localhost:8005/health"
check_ms "ms-006 ai-feedback"    8006 "/api/v1/ai-feedback/health" 2>/dev/null || check_http "ms-006 ai-feedback"  "http://localhost:8006/health"
check_ms "ms-007 feedback"       8007 "/api/v1/feedback/health"  2>/dev/null || check_http "ms-007 feedback"       "http://localhost:8007/health"
check_ms "ms-008 pdf-export"     8008 "/api/v1/pdf/health"       2>/dev/null || check_http "ms-008 pdf-export"     "http://localhost:8008/health"
check_ms "ms-009 audit"          8009 "/api/v1/audit/health"     2>/dev/null || check_http "ms-009 audit"          "http://localhost:8009/health"
check_ms "ms-010 consent"        8010 "/api/v1/consent/health"   2>/dev/null || check_http "ms-010 consent"        "http://localhost:8010/health"
check_ms "ms-011 knowledge"      8011 "/api/v1/knowledge/health" 2>/dev/null || check_http "ms-011 knowledge"      "http://localhost:8011/health"
check_ms "ms-012 best-practices" 8012 "/api/v1/best-practices/health" 2>/dev/null || check_http "ms-012 best-practices" "http://localhost:8012/health"

# Simplified version: just check all direct ports
echo ""
echo "Microservices (direct ports)"
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8009 8010; do
  check_http "  :$port" "http://localhost:$port/health"
done
check_http "  :8011 (knowledge)"       "http://localhost:8011/health"
check_http "  :8012 (best-practices)"  "http://localhost:8012/health"

# Infrastructure (optional — only available locally)
echo ""
echo "Infrastructure"
if command -v psql &>/dev/null 2>&1; then
  PGPASSWORD="${POSTGRES_PASSWORD:-}" psql -U "${POSTGRES_USER:-pec}" -h localhost -c '\q' &>/dev/null && \
    pass "postgres (port 5432)" || fail "postgres (port 5432)"
else
  skip "postgres (psql not installed)"
fi

if command -v redis-cli &>/dev/null 2>&1; then
  redis-cli ping &>/dev/null && pass "redis (port 6379)" || fail "redis (port 6379)"
else
  skip "redis (redis-cli not installed)"
fi

curl -sf --max-time "$TIMEOUT" "http://localhost:9000/minio/health/live" &>/dev/null && \
  pass "minio (port 9000)" || fail "minio (port 9000)"

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $FAILED -eq 0 ]]; then
  echo -e "${GREEN}All checks passed ✓${NC}"
  exit 0
else
  echo -e "${RED}${FAILED} check(s) failed ✗${NC}"
  exit 1
fi
