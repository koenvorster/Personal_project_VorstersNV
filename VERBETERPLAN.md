# 📋 VorstersNV Verbeterplan

Gegenereerd op basis van codebase-analyse. Werk deze items af met je AI fleet.

## 🔴 Prioriteit 1 — Directe fixes

- [ ] **mcp-server versies synchroniseren**: `mcp-server/requirements.txt` gebruikt FastAPI 0.104.1 / httpx 0.25.0 / pydantic 2.5.0 — synchroniseer met root `requirements.txt` (FastAPI 0.115.6, httpx 0.28.1, pydantic 2.10.4)
- [ ] **Dubbele httpx vermelding verwijderen** in `requirements.txt` (regel 27: `httpx  # al hierboven` weggooien)
- [ ] **Echte screenshots toevoegen** aan `docs/screenshots/` (homepage, dashboard, projecten, login, swagger) en README-placeholders vervangen
- [ ] **README badge "28 tests" updaten** naar het correcte aantal (45+ testbestanden aanwezig)

## 🟡 Prioriteit 2 — Architectuur & Documentatie

- [ ] **LICENSE bestand toevoegen** (bijv. proprietary / All Rights Reserved)
- [ ] **Backend-scheiding documenteren**: FastAPI vs Spring Boot — welke bounded context hoort waar? Maak dit expliciet in de README en architectuurdocumentatie
- [ ] **Productie-URL invullen** in `.claude/README.md` (momenteel `TBD`)
- [ ] **Keycloak setup documenteren** in `keycloak/README.md` — realm-naam, client-id, redirect URIs, stap-voor-stap voor nieuwe developers

## 🟢 Prioriteit 3 — CI/CD & Kwaliteit

- [ ] **pip-cache toevoegen aan GitHub Actions** in `.github/workflows/ci.yml`:
  ```yaml
  - uses: actions/cache@v4
    with:
      path: ~/.cache/pip
      key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
  ```
- [ ] **`pyproject.toml` uitbreiden** met:
  - `[tool.pytest.ini_options]` met `asyncio_mode = "auto"`
  - `[tool.mypy]` stricte instellingen
  - `[tool.ruff.lint]` regels
- [ ] **Frontend `AGENTS.md` linken** in de hoofd-README onder het frontend-gedeelte

## 💡 Prioriteit 4 — Security & Developer Experience

- [ ] **`gitleaks` of `trufflehog` toevoegen** als secret-scanning stap in CI (`.github/workflows/ci.yml`)
- [ ] **`CONTRIBUTING.md` aanmaken** met ontwikkelaarsgids, branch-strategie, commit-conventies
- [ ] **Ollama mock-fixture toevoegen** aan `tests/conftest.py` voor tests die Ollama-aanroepen simuleren zonder actieve server

## ✅ Al goed — niet aanpassen
- HMAC-beveiliging webhooks ✅
- `.env.example` aanwezig ✅
- Dev Container geconfigureerd ✅
- GDPR/compliance engine aanwezig ✅
- GitHub Actions workflows aanwezig ✅
- Brede testsuite (45+ bestanden) ✅
