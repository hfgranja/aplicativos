# Deploy Guide — PEC Observation App

## Backend → Google Cloud Run

### Pré-requisitos
- Conta GCP com billing ativado
- `gcloud` CLI instalado e autenticado
- `terraform` >= 1.5 instalado
- Docker instalado

### 1. Bootstrap do projeto GCP

```bash
# Crie ou use um projeto GCP existente
gcloud projects create pec-observation-prod --name="PEC Observation"
gcloud config set project pec-observation-prod

# Execute o script de setup (cria bucket de estado Terraform, habilita APIs)
bash infra/scripts/setup-gcp.sh pec-observation-prod pec-obs-terraform-state
```

### 2. Configurar variáveis Terraform

```bash
cd infra/gcp/terraform
cp terraform.tfvars.example terraform.tfvars
# Edite terraform.tfvars com seu project_id, senhas e JWT secret
```

### 3. Aplicar infraestrutura

```bash
terraform init -backend-config="bucket=pec-obs-terraform-state"
terraform plan
terraform apply
```

Isso cria:
- Cloud SQL Postgres (10 databases)
- Memorystore Redis
- GCS buckets (audio-uploads, pdf-exports)
- Artifact Registry
- VPC + Connector serverless
- Secret Manager
- 10 Cloud Run services

### 4. Popular secrets com senhas

```bash
bash infra/scripts/seed-secrets.sh pec-observation-prod
```

### 5. Conectar Cloud Build ao GitHub

No GCP Console: **Cloud Build → Triggers → Connect repository**
- Repositório: `hfgranja/aplicativos`
- Branch: `^main$`
- cloudbuild.yaml: `pec-observation-app/infra/gcp/cloudbuild/cloudbuild.yaml`

### 6. Primeiro deploy manual

```bash
# Build e push inicial de todas as imagens
cd pec-observation-app
REGISTRY=$(terraform -chdir=infra/gcp/terraform output -raw artifact_registry_url)

for svc in ms-001-identity ms-002-school ms-003-observation \
           ms-004-audio-ingestion ms-005-transcription \
           ms-006-ai-feedback ms-007-feedback ms-008-pdf-export \
           ms-009-audit ms-010-consent; do
  docker build -t "$REGISTRY/$svc:latest" -f "services/$svc/Dockerfile" .
  docker push "$REGISTRY/$svc:latest"
done

# Deploy
gcloud run services update pec-obs-ms-001-identity \
  --image="$REGISTRY/ms-001-identity:latest" \
  --region=southamerica-east1
# (repita para cada serviço ou use o cloudbuild trigger)
```

### 7. Configurar GitHub Actions

Adicione estes secrets no repositório GitHub:
| Secret | Como obter |
|--------|-----------|
| `GCP_PROJECT_ID` | ID do seu projeto GCP |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `gcloud iam workload-identity-pools providers describe ...` |
| `GCP_SERVICE_ACCOUNT` | Email da SA criada pelo Terraform (ver `terraform output`) |
| `SLACK_WEBHOOK` | Opcional — webhook do Slack para notificações |

Para Workload Identity Federation (sem chave JSON):
```bash
gcloud iam workload-identity-pools create github \
  --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"

gcloud iam service-accounts add-iam-policy-binding \
  "$(terraform -chdir=infra/gcp/terraform output -raw service_account_email)" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/hfgranja/aplicativos"
```

---

## iOS App → Apple App Store

### Pré-requisitos
- Mac com Xcode 15+ instalado
- Apple Developer Account ($99/ano) — https://developer.apple.com
- Conta App Store Connect criada para o app

### 1. Criar app no App Store Connect

1. Acesse https://appstoreconnect.apple.com
2. **Apps → (+) Nova App**
   - Plataforma: iOS
   - Nome: PEC Observação
   - Bundle ID: `br.gov.educacao.sp.pec-observation`
   - SKU: `pec-observation-2024`
3. Preencha informações de privacidade, classificação, etc.

### 2. Configurar Fastlane Match (code signing)

```bash
# Crie um repositório Git PRIVADO para armazenar certificados
# Ex: github.com/suaorg/pec-obs-certificates

cd pec-observation-app/ios-app
gem install bundler
bundle install

# Inicializar match (primeira vez — cria os certificados)
bundle exec fastlane match init
bundle exec fastlane match appstore
```

### 3. Configurar variáveis de ambiente

Copie para `~/.zshrc` ou configure no CI:
```bash
export APPLE_ID="seu@email.com"
export TEAM_ID="XXXXXXXXXX"        # Apple Developer Team ID
export ITC_TEAM_ID="XXXXXXXXXX"    # App Store Connect Team ID
export APPLE_APP_ID="XXXXXXXXXX"   # App Store Connect App ID numérico
export MATCH_GIT_URL="https://github.com/suaorg/pec-obs-certificates"
export MATCH_PASSWORD="senha-do-repositorio-de-certificados"
```

### 4. Gerar App Store Connect API Key

1. App Store Connect → Users and Access → Integrations → App Store Connect API
2. Crie uma chave com role "App Manager"
3. Baixe o arquivo `.p8`

### 5. GitHub Actions secrets (iOS)

| Secret | Valor |
|--------|-------|
| `APPLE_ID` | seu@email.com |
| `TEAM_ID` | Apple Developer Team ID |
| `ITC_TEAM_ID` | App Store Connect Team ID |
| `APPLE_APP_ID` | ID numérico do app no ASC |
| `MATCH_GIT_URL` | URL do repo de certificados |
| `MATCH_PASSWORD` | Senha do match |
| `ASC_KEY_ID` | ID da API Key |
| `ASC_ISSUER_ID` | Issuer ID da API Key |
| `ASC_PRIVATE_KEY` | Conteúdo do arquivo .p8 |

### 6. Primeiro build manual

```bash
cd pec-observation-app/ios-app

# Instalar certificados localmente (readonly: false)
MATCH_READONLY=false bundle exec fastlane match appstore

# Build + TestFlight
bundle exec fastlane beta
```

### 7. CI automático

Após configurar os secrets:
- **Push para `main`** com mudança no `ios-app/` → build automático para TestFlight
- **Tag `ios-v1.0.0`** → build + submissão para revisão da Apple

```bash
git tag ios-v1.0.0
git push origin ios-v1.0.0
```

### 8. Atualizar URL do backend no app

Antes de submeter, atualize `PEC_API_BASE_URL` no `Info.plist` do Xcode apontando para a URL do Cloud Run do MS-001 Identity:

```bash
terraform -chdir=pec-observation-app/infra/gcp/terraform output cloud_run_urls
```

---

## Resumo dos custos estimados (GCP)

| Serviço | Estimativa mensal |
|---------|------------------|
| Cloud Run (10 serviços, min=0) | ~$0–30 |
| Cloud SQL db-g1-small | ~$25 |
| Memorystore Redis 1GB BASIC | ~$35 |
| GCS (áudio 7 dias + PDF) | ~$5 |
| Artifact Registry | ~$2 |
| Egress + outros | ~$5 |
| **Total estimado** | **~$70–100/mês** |

Para escala: aumente `db_tier` para `db-custom-2-7680` e Redis para `STANDARD_HA`.
