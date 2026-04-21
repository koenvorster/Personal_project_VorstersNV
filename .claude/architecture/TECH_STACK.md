# Tech Stack — VorstersNV (Source of Truth)

> **Dit is de canonieke bron voor tech stack versies.**
> Verwijs naar dit bestand vanuit CLAUDE.md en copilot-instructions.md.
> Update dit bestand als een versie wijzigt.

_Laatste update: 2025 — automatisch controleerbaar via `frontend/package.json` en `pyproject.toml`_

## Versies

| Laag | Technologie | Versie | Locatie |
|------|-------------|--------|---------|
| **Frontend** | Next.js | **16.2.2** | `frontend/package.json` |
| **Frontend** | TypeScript | strict | `frontend/tsconfig.json` |
| **Frontend** | Tailwind CSS | 3.x | `frontend/tailwind.config.ts` |
| **Backend** | Python | **3.12** | `pyproject.toml` |
| **Backend** | FastAPI | async | `api/main.py` |
| **Backend** | SQLAlchemy | 2.x (async) | `requirements.txt` |
| **Backend** | Pydantic | v2 | `requirements.txt` |
| **Backend Java** | Spring Boot | 3.3.5 (legacy) | `backend/pom.xml` |
| **Backend Java** | Java | 21 (legacy) | `backend/pom.xml` |
| **Database** | PostgreSQL | 16 | `docker-compose.yml` |
| **Cache** | Redis | 7 | `docker-compose.yml` |
| **AI** | Ollama | lokaal | `docker-compose.yml` |
| **AI Models** | mistral | latest (Q4_K_M) | `agents/*.yml` |
| **AI Models** | llama3.2 | latest (Q4_K_M) | `agents/*.yml` |
| **Auth** | Keycloak | dev | `docker-compose.yml` |
| **CI/CD** | GitHub Actions | — | `.github/workflows/` |
| **Linter** | Ruff | E,F,W,I | `pyproject.toml` |
| **Type Check** | mypy | strict | `pyproject.toml` |

## Architecture Pattern

```
Frontend (Next.js 16.2)
    │ fetch('/api/v1/...')
    ▼
Backend API (FastAPI :8000)  ← PRIMAIRE BACKEND
    │ SQLAlchemy async
    ▼
PostgreSQL 16 + Redis 7
    │
    ├── Mollie API (betalingen)
    ├── Ollama :11434 (lokale AI-agents)
    └── Keycloak (auth, dev)

Legacy: Spring Boot :8080 → NIET voor nieuwe features
```

## Hosting (Productie — TBD)

| Service | Plan | Status |
|---------|------|--------|
| Frontend | Vercel / Cloud Run | Niet uitgerold |
| API | Cloud Run (GCP) | Niet uitgerold |
| Database | Cloud SQL / Supabase | Niet uitgerold |
| Ollama | Gaming desktop LAN server | In planning |
