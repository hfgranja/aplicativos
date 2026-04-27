# PEC Observation App — Makefile
# Requires: docker, docker compose v2, curl, openssl
#
# Development:   make up
# Production:    make prod-up

COMPOSE     = docker compose
COMPOSE_DEV = $(COMPOSE) -f docker-compose.yml
COMPOSE_PROD= $(COMPOSE) -f docker-compose.prod.yml --env-file .env.production
PROJECT     = pec-obs

# ── Development ───────────────────────────────────────────────────────────────

.PHONY: up
up: ## Start all dev services
	$(COMPOSE_DEV) up -d

.PHONY: down
down: ## Stop all dev services
	$(COMPOSE_DEV) down

.PHONY: build
build: ## Build dev images
	$(COMPOSE_DEV) build

.PHONY: logs
logs: ## Tail logs (all services)
	$(COMPOSE_DEV) logs -f --tail=100

.PHONY: ps
ps: ## Show service status
	$(COMPOSE_DEV) ps

# ── Production ────────────────────────────────────────────────────────────────

.PHONY: prod-build
prod-build: ## Build all production images (takes ~10 min first time)
	@echo "→ Building production images (context = project root)..."
	$(COMPOSE_PROD) build --parallel
	@echo "✓ Build complete"

.PHONY: prod-up
prod-up: ## Start production stack (builds if needed)
	@test -f .env.production || (echo "ERROR: .env.production missing. Copy and fill it first." && exit 1)
	$(COMPOSE_PROD) up -d
	@echo "✓ Production stack started"
	@echo "  Web app: http://$(shell hostname -I | awk '{print $$1}')"

.PHONY: prod-down
prod-down: ## Stop production stack
	$(COMPOSE_PROD) down

.PHONY: prod-restart
prod-restart: ## Rolling restart of all services (zero-downtime if replicas > 1)
	$(COMPOSE_PROD) up -d --no-deps --build

.PHONY: prod-logs
prod-logs: ## Tail production logs
	$(COMPOSE_PROD) logs -f --tail=100

.PHONY: prod-ps
prod-ps: ## Show production service status
	$(COMPOSE_PROD) ps

.PHONY: prod-deploy
prod-deploy: ## Full deploy: pull latest, build, recreate services
	@bash scripts/deploy.sh

# ── Health & Monitoring ───────────────────────────────────────────────────────

.PHONY: health
health: ## Check health of all services (dev)
	@bash scripts/health-check.sh http://localhost

.PHONY: prod-health
prod-health: ## Check health of production services
	@bash scripts/health-check.sh http://localhost

# ── Database ─────────────────────────────────────────────────────────────────

.PHONY: backup
backup: ## Backup all Postgres databases + MinIO
	@bash scripts/backup.sh

.PHONY: restore
restore: ## Restore from backup (BACKUP_FILE=path/to/backup.tar.gz)
	@test -n "$(BACKUP_FILE)" || (echo "Usage: make restore BACKUP_FILE=path/to/backup.tar.gz" && exit 1)
	@bash scripts/restore.sh $(BACKUP_FILE)

# ── Secrets ───────────────────────────────────────────────────────────────────

.PHONY: gen-secrets
gen-secrets: ## Generate random secrets and print them (do not save to repo)
	@echo "SECRET_KEY=$(shell openssl rand -hex 32)"
	@echo "POSTGRES_PASSWORD=$(shell openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"
	@echo "MINIO_ROOT_PASSWORD=$(shell openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)"

# ── Utilities ─────────────────────────────────────────────────────────────────

.PHONY: shell
shell: ## Open a shell in a service (SVC=ms-001-identity)
	$(COMPOSE_DEV) exec $(SVC) /bin/bash

.PHONY: prod-shell
prod-shell: ## Open a shell in a production service (SVC=ms-001-identity)
	$(COMPOSE_PROD) exec $(SVC) /bin/bash

.PHONY: clean
clean: ## Remove all containers, volumes, and images (DESTRUCTIVE)
	@read -p "This will DELETE all data. Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	$(COMPOSE_DEV) down -v --rmi local
	$(COMPOSE_PROD) down -v --rmi local 2>/dev/null || true

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
