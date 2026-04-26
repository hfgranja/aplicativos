#!/usr/bin/env bash
# One-time GCP project bootstrap.
# Run: bash infra/scripts/setup-gcp.sh YOUR_PROJECT_ID YOUR_STATE_BUCKET
set -euo pipefail

PROJECT_ID="${1:?Usage: setup-gcp.sh PROJECT_ID STATE_BUCKET}"
STATE_BUCKET="${2:?Usage: setup-gcp.sh PROJECT_ID STATE_BUCKET}"
REGION="southamerica-east1"
APP_NAME="pec-obs"

echo "==> Setting project: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

echo "==> Creating Terraform state bucket"
gcloud storage buckets create "gs://$STATE_BUCKET" \
  --location="$REGION" \
  --uniform-bucket-level-access \
  --public-access-prevention \
  2>/dev/null || echo "Bucket already exists, skipping"

gcloud storage buckets update "gs://$STATE_BUCKET" \
  --versioning

echo "==> Enabling billing (ensure billing account is linked in console)"
# gcloud billing projects link $PROJECT_ID --billing-account=BILLING_ACCOUNT_ID

echo "==> Connecting Cloud Build trigger to GitHub repository"
echo "    Configure this manually in GCP Console:"
echo "    Cloud Build > Triggers > Connect repository > GitHub"
echo "    Branch: ^main$"
echo "    cloudbuild.yaml: pec-observation-app/infra/gcp/cloudbuild/cloudbuild.yaml"

echo "==> Initialising Terraform"
cd "$(dirname "$0")/../gcp/terraform"
terraform init -backend-config="bucket=$STATE_BUCKET"

echo "==> Creating terraform.tfvars (copy from example and fill in)"
if [[ ! -f terraform.tfvars ]]; then
  cp terraform.tfvars.example terraform.tfvars
  echo ""
  echo "  *** IMPORTANT: edit infra/gcp/terraform/terraform.tfvars before continuing ***"
  echo ""
fi

echo "==> Done. Next steps:"
echo "  1. Edit infra/gcp/terraform/terraform.tfvars"
echo "  2. cd infra/gcp/terraform && terraform plan"
echo "  3. terraform apply"
echo "  4. Connect Cloud Build trigger in console"
