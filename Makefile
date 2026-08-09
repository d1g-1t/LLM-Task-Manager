SHELL := /bin/bash
COMPOSE ?= docker compose
BACKEND := $(COMPOSE) exec -T backend
FRONTEND := $(COMPOSE) exec -T frontend

.DEFAULT_GOAL := help
.PHONY: help setup demo open health env build up down restart logs ps \
        migrate makemigration seed shell-backend shell-frontend \
        backend-install frontend-install \
        test test-backend test-frontend coverage \
        lint lint-backend lint-frontend format \
        typecheck clean nuke

help: ## Show this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1mTargets\033[0m\n"} \
	  /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' \
	  $(MAKEFILE_LIST)

env: ## Create .env from .env.example if it does not exist.
	@test -f .env || (cp .env.example .env && echo "✔ .env created from .env.example")

setup: env ## One-shot bootstrap: build images, start stack, run migrations.
	@echo "▶ Building images..."
	@$(COMPOSE) build --pull
	@echo "▶ Starting infrastructure (postgres, redis)..."
	@$(COMPOSE) up -d postgres redis
	@echo "▶ Waiting for postgres to become healthy..."
	@until $(COMPOSE) exec -T postgres pg_isready -U $${POSTGRES_USER:-todo} >/dev/null 2>&1; do sleep 1; done
	@echo "▶ Starting backend & frontend..."
	@$(COMPOSE) up -d backend frontend
	@echo "▶ Applying migrations..."
	@$(COMPOSE) exec -T backend alembic upgrade head
	@echo "▶ Seeding demo data..."
	@$(COMPOSE) exec -T backend python -m app.scripts.seed
	@echo ""
	@echo "✔ Stack is up:"
	@echo "    Frontend  → http://localhost:3000"
	@echo "    Backend   → http://localhost:8000/api/v1"
	@echo "    Docs      → http://localhost:8000/docs"

demo: setup open ## Bootstrap the stack AND open the frontend in a browser.

open: ## Open the frontend in the default browser (cross-platform).
	@(command -v xdg-open >/dev/null && xdg-open http://localhost:3000) \
	  || (command -v open >/dev/null && open http://localhost:3000) \
	  || (command -v powershell.exe >/dev/null && powershell.exe -Command "Start-Process http://localhost:3000") \
	  || echo "Open http://localhost:3000 in your browser"

health: ## Quick smoke check (containers + API health endpoint).
	@$(COMPOSE) ps
	@echo "---"
	@curl -fsS http://localhost:8000/api/v1/health && echo " ✔ backend healthy" || echo "✘ backend unhealthy"

build: ## Rebuild docker images.
	$(COMPOSE) build

up: ## Start the stack in the background.
	$(COMPOSE) up -d

down: ## Stop the stack (preserves volumes).
	$(COMPOSE) down

restart: down up ## Restart the whole stack.

logs: ## Tail logs from all services.
	$(COMPOSE) logs -f --tail=100

ps: ## Show container status.
	$(COMPOSE) ps

migrate: ## Apply latest alembic migrations.
	$(BACKEND) alembic upgrade head

makemigration: ## Autogenerate a new migration. Usage: make makemigration m="add field"
	$(BACKEND) alembic revision --autogenerate -m "$(m)"

seed: ## Seed the database with demo data.
	$(BACKEND) python -m app.scripts.seed

shell-backend: ## Open a shell in the backend container.
	$(COMPOSE) exec backend bash

shell-frontend: ## Open a shell in the frontend container.
	$(COMPOSE) exec frontend sh

test: test-backend test-frontend ## Run the full test suite.

test-backend: ## Run backend tests (pytest).
	$(BACKEND) pytest -q

test-frontend: ## Run frontend tests (vitest).
	$(FRONTEND) npm run test -- --run

coverage: ## Backend test coverage report.
	$(BACKEND) pytest --cov=app --cov-report=term-missing --cov-report=xml

lint: lint-backend lint-frontend ## Run all linters.

lint-backend: ## Lint backend (ruff + mypy).
	$(BACKEND) ruff check .
	$(BACKEND) mypy app

lint-frontend: ## Lint frontend (eslint + tsc).
	$(FRONTEND) npm run lint
	$(FRONTEND) npm run typecheck

format: ## Auto-format code (ruff + prettier).
	$(BACKEND) ruff format .
	$(BACKEND) ruff check . --fix
	$(FRONTEND) npm run format

typecheck: ## Static type checks.
	$(BACKEND) mypy app
	$(FRONTEND) npm run typecheck

clean: ## Remove caches and build artifacts on host.
	@find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache -o -name .next -o -name coverage -o -name htmlcov \) -prune -exec rm -rf {} +

nuke: ## Stop stack and remove volumes (DESTROYS DB DATA).
	$(COMPOSE) down -v --remove-orphans
