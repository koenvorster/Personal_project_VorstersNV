---
paths:
  - "docker-compose.yml"
  - "Dockerfile*"
  - ".devcontainer/**"
---

# Docker Conventies — VorstersNV

## Vaste Poorten — VERPLICHT

Wijzig nooit de servicepoorten zonder overleg. Dit zijn de vastgestelde poorten:

| Service | Host-poort | Container-poort | Beschrijving |
|---------|-----------|-----------------|-------------|
| Next.js | 3000 | 3000 | Frontend webshop |
| FastAPI | 8000 | 8000 | REST API + webhooks |
| PostgreSQL | 5432 | 5432 | Hoofddatabase |
| Redis | 6379 | 6379 | Cache |
| Keycloak | 8080 | 8080 | Auth server (dev) |
| Ollama | 11434 | 11434 | AI model server |

---

## Health Checks — VERPLICHT

Elke service in `docker-compose.yml` heeft een `healthcheck`:

```yaml
# GOED
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

# SLECHT — geen health check
services:
  api:
    image: vorsternv-api:latest
    # ontbrekende healthcheck
```

---

## Geen Secrets in Dockerfile — VERPLICHT

```dockerfile
# GOED — secrets via omgevingsvariabelen op runtime
ENV DATABASE_URL=""
ENV MOLLIE_API_KEY=""

# SLECHT — hardcoded secret in image
ENV MOLLIE_API_KEY="live_abc123..."
RUN echo "password123" | ...
```

Gebruik altijd `.env` of Docker secrets voor gevoelige waarden. Het `.env` bestand staat
in `.gitignore` en mag NOOIT worden gecommit.

---

## Multi-stage Builds — AANBEVOLEN

```dockerfile
# Stap 1: Build stage
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stap 2: Runtime stage (kleinere image)
FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## depends_on met condition — STRICT

```yaml
# GOED — wacht op echte health
services:
  api:
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

# SLECHT — wacht alleen op start, niet op beschikbaarheid
services:
  api:
    depends_on:
      - postgres
      - redis
```

---

## Volumes Naamgeving — VERPLICHT

Gebruik beschrijvende namen voor named volumes:

```yaml
volumes:
  vorsternv_postgres_data:
    driver: local
  vorsternv_redis_data:
    driver: local
  vorsternv_ollama_models:
    driver: local
```

---

## Niet wijzigen zonder overleg

- `docker-compose.yml` servicepoorten
- PostgreSQL volume configuratie (risico op dataverlies)
- Keycloak realm configuratie
- Ollama model directory
