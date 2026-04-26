#!/usr/bin/env bash
# Seeds Secret Manager values after terraform apply.
# Usage: bash infra/scripts/seed-secrets.sh PROJECT_ID
set -euo pipefail

PROJECT_ID="${1:?Usage: seed-secrets.sh PROJECT_ID}"
APP_NAME="pec-obs"

secret() {
  local name="$1"
  local prompt="$2"
  local secret_id="${APP_NAME}-${name}"

  if gcloud secrets versions access latest --secret="$secret_id" --project="$PROJECT_ID" &>/dev/null; then
    echo "  [skip] $secret_id already has a version"
    return
  fi

  read -rsp "  Enter value for $prompt: " value
  echo
  printf '%s' "$value" | gcloud secrets versions add "$secret_id" \
    --data-file=- --project="$PROJECT_ID"
  echo "  [ok] $secret_id set"
}

echo "==> Seeding secrets for project: $PROJECT_ID"
echo ""
echo "  Terraform creates the secret resources but leaves them empty."
echo "  This script fills in the actual values."
echo ""

secret "jwt-secret-key"   "JWT secret key (hex, min 32 chars)"
secret "db-password"      "PostgreSQL master password"

echo ""
echo "==> Note: minio-access-key and minio-secret-key are auto-seeded"
echo "    by Terraform from the GCS HMAC key."
echo ""
echo "==> Done. Run 'gcloud secrets list --project=$PROJECT_ID' to verify."
