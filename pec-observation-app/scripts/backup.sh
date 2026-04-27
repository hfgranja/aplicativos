#!/usr/bin/env bash
# PEC Observation App — Backup Script
# Creates a timestamped backup of all Postgres databases + MinIO objects.
#
# Usage: bash scripts/backup.sh [--dest /path/to/backups]
# Output: backups/pec-backup-YYYYMMDD-HHMMSS.tar.gz

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEST="${1:-$ROOT/backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TMP_DIR=$(mktemp -d)
BACKUP_NAME="pec-backup-${TIMESTAMP}"
BACKUP_DIR="$TMP_DIR/$BACKUP_NAME"

# Load env
[[ -f "$ROOT/.env.production" ]] && source "$ROOT/.env.production" 2>/dev/null || true

POSTGRES_USER="${POSTGRES_USER:-pec}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-pec_secret}"
COMPOSE="docker compose -f $ROOT/docker-compose.prod.yml --env-file $ROOT/.env.production"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }

mkdir -p "$BACKUP_DIR/postgres" "$BACKUP_DIR/minio" "$DEST"

echo "PEC Observation App — Backup"
echo "Timestamp: $TIMESTAMP"
echo "Destination: $DEST"
echo ""

# ── Postgres ─────────────────────────────────────────────────────────────────
echo "→ Dumping Postgres databases..."
DATABASES=(
  pec_identity pec_school pec_observation pec_audio pec_transcription
  pec_ai_feedback pec_feedback pec_pdf pec_audit pec_consent
  pec_knowledge pec_best_practices
)

for db in "${DATABASES[@]}"; do
  echo -n "  $db..."
  $COMPOSE exec -T postgres pg_dump \
    -U "$POSTGRES_USER" \
    --format=custom \
    --compress=9 \
    "$db" > "$BACKUP_DIR/postgres/${db}.dump" 2>/dev/null && \
    echo " done" || warn " FAILED (database may not exist yet)"
done
ok "Postgres dump complete"

# ── MinIO ─────────────────────────────────────────────────────────────────────
echo "→ Backing up MinIO buckets..."
BUCKETS=(audio-uploads pdf-exports best-practices)

for bucket in "${BUCKETS[@]}"; do
  echo -n "  $bucket..."
  $COMPOSE exec -T minio mc alias set local http://localhost:9000 \
    "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" &>/dev/null || true
  # Use mc mirror to copy bucket contents
  docker run --rm \
    --network "$(docker network ls --filter name=pec-network --format '{{.Name}}' | head -1)" \
    -v "$BACKUP_DIR/minio:/backup" \
    --entrypoint /bin/sh \
    minio/mc:latest -c "
      mc alias set local http://minio:9000 ${MINIO_ROOT_USER:-minioadmin} ${MINIO_ROOT_PASSWORD:-minioadmin} 2>/dev/null
      mc mirror local/${bucket} /backup/${bucket} 2>/dev/null || true
    " && echo " done" || warn " FAILED (bucket may be empty or unreachable)"
done
ok "MinIO backup complete"

# ── Metadata ─────────────────────────────────────────────────────────────────
cat > "$BACKUP_DIR/manifest.json" <<EOF
{
  "timestamp":    "$TIMESTAMP",
  "hostname":     "$(hostname)",
  "databases":    $(printf '"%s",' "${DATABASES[@]}" | sed 's/,$//' | awk '{print "["$0"]"}'),
  "minio_buckets":$(printf '"%s",' "${BUCKETS[@]}" | sed 's/,$//' | awk '{print "["$0"]"}'),
  "pec_version":  "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
}
EOF

# ── Compress ──────────────────────────────────────────────────────────────────
echo "→ Compressing backup..."
ARCHIVE="$DEST/${BACKUP_NAME}.tar.gz"
tar -czf "$ARCHIVE" -C "$TMP_DIR" "$BACKUP_NAME"
rm -rf "$TMP_DIR"

SIZE=$(du -sh "$ARCHIVE" | cut -f1)
ok "Backup saved: $ARCHIVE ($SIZE)"

# ── Retention: keep last 7 backups ───────────────────────────────────────────
echo "→ Pruning old backups (keeping 7 most recent)..."
ls -t "$DEST"/pec-backup-*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null || true
REMAINING=$(ls "$DEST"/pec-backup-*.tar.gz 2>/dev/null | wc -l)
ok "Backup rotation complete ($REMAINING backups retained)"
