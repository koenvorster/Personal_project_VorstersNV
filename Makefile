# VorstersNV – Makefile
# Gebruik: make <target>

.PHONY: up down api webhooks frontend test lint mypy typecheck coverage migrate migrate-analytics migration migration-analytics mode build-mode validate-agents

## Start alle services (Ollama, PostgreSQL, Redis, Webhooks)
up:
	docker-compose up -d

## Stop alle services
down:
	docker-compose down

## Start de REST API lokaal
api:
	uvicorn api.main:app --reload --port 8000

## Start de webhook service lokaal
webhooks:
	uvicorn webhooks.app:app --reload --port 8001

## Start de Next.js frontend
frontend:
	cd frontend && npm run dev

## Draai alle Python tests
test:
	python3 -m pytest tests/ -v --tb=short

## Draai tests met coverage rapport
coverage:
	python3 -m pytest tests/ -v --cov=api --cov=ollama --cov-report=term-missing

## Draai linter (Ruff)
lint:
	ruff check .

## Draai type-checker (mypy)
mypy:
	mypy api/ ollama/ --ignore-missing-imports

## Alias voor mypy
typecheck: mypy

## Webshop DB migratie uitvoeren
migrate:
	alembic -c alembic.ini upgrade head

## Analytics DB migratie uitvoeren
migrate-analytics:
	alembic -c alembic_analytics.ini upgrade head

## Nieuwe migratie aanmaken (webshop DB)
migration:
	alembic -c alembic.ini revision --autogenerate -m "$(msg)"

## Nieuwe migratie aanmaken (analytics DB)
migration-analytics:
	alembic -c alembic_analytics.ini revision --autogenerate -m "$(msg)"

## Toon project mode
mode:
	python3 scripts/set_mode.py --status

## Zet op build mode
build-mode:
	python3 scripts/set_mode.py --mode build

## Valideer alle Claude agents met validate-agents.mjs
validate-agents:
	node .claude/scripts/validate-agents.mjs
