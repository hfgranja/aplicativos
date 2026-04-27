#!/usr/bin/env bash
# PEC Observation App — Restore Script
# Restores Postgres databases and MinIO objects from a backup archive.
#
# Usage: bash scripts/restore.sh /path/to/pec-backup-YYYYMMDD-HHMMSS.tar.gz
#
# WARNING: This OVERWRITES existing data. Confirm before running in production.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ARCHIVE="${1:-}"
if [[ -z "$ARCHIVE" ]]; then
  echo "Usage: bash scripts/restore.sh /path/to/pec-backup-YYYYMMDD-HHMMSS.tar.gz"
  exit 1
fi
[[ -f "$ARCHIVE" ]] || { echo "ERROR: archive not found: $ARCHIVE"; exit 1; }

# Load env
[[ -f "$ROOT/.env.production" ]] && source "$ROOT/.env.production" 2>/dev/null || true

POSTGRES_USER="${POSTGRES_USER:-pec}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-pec_secret}"
COMPOSE="docker compose -f $ROOT/docker-compose.prod.yml --env-file $ROOT/.env.production"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

echo "PEC Observation App — Restore"
echo "Archive: $ARCHIVE"
echo ""

# ── Confirm ───────────────────────────────────────────────────────────────────
read -r -p "This will OVERWRITE existing databases and MinIO objects. Continue? [y/N] " confirm
[[ "${confirm,,}" == "y" ]] || { echo "Aborted."; exit 0; }

# ── Extract ───────────────────────────────────────────────────────────────────
echo "→ Extracting archive..."
tar -xzf "$ARCHIVE" -C "$TMP_DIR"
BACKUP_DIR=$(find "$TMP_DIR" -maxdepth 1 -type d -name "pec-backup-*" | head -1)
[[ -d "$BACKUP_DIR" ]] || err "Could not find backup directory inside archive"

# Show manifest if present
if [[ -f "$BACKUP_DIR/manifest.json" ]]; then
  echo "  Manifest:"
  cat "$BACKUP_DIR/manifest.json" | sed 's/^/    /'
  echo ""
fi

# ── Postgres ──────────────────────────────────────────────────────────────────
echo "→ Restoring Postgres databases..."
for dump_file in "$BACKUP_DIR/postgres/"*.dump; do
  [[ -f "$dump_file" ]] || continue
  db=$(basename "$dump_file" .dump)
  echo -n "  $db..."
  # Drop and recreate the database, then restore
  $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${db}' AND pid <> pg_backend_pid();" \
    postgres &>/dev/null || true
  $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -c \
    "DROP DATABASE IF EXISTS ${db};" postgres &>/dev/null || true
  $COMPOSE exec -T postgres psql -U "$POSTGRES_USER" -c \
    "CREATE DATABASE ${db};" postgres &>/dev/null || true
  $COMPOSE exec -T postgres pg_restore \
    -U "$POSTGRES_USER" \
    --no-privileges \
    --no-owner \
    -d "$db" < "$dump_file" 2>/dev/null && \
    echo " done" || warn " completed with warnings"
done
ok "Postgres restore complete"

# ── MinIO ─────────────────────────────────────────────────────────────────────
echo "→ Restoring MinIO buckets..."
NETWORK=$(docker network ls --filter name=pec-network --format '{{.Name}}' | head -1)

for bucket_dir in "$BACKUP_DIR/minio/"*/; do
  [[ -d "$bucket_dir" ]] || continue
  bucket=$(basename "$bucket_dir")
  echo -n "  $bucket..."
  docker run --rm \
    --network "${NETWORK:-bridge}" \
    -v "$bucket_dir:/restore/${bucket}:ro" \
    --entrypoint /bin/sh \
    minio/mc:latest -c "
      mc alias set local http://minio:9000 ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin} 2>/dev/null
      mc mb --ignore-existing local/${bucket} 2>/dev/null || true
      mc mirror /restore/${bucket} local/${bucket} 2>/dev/null || true
    " && echo " done" || warn " FAILED (MinIO may be unreachable)"
done
ok "MinIO restore complete"

echo ""
ok "Restore finished. Restart services if needed: make prod-restart"
