---
name: env-audit
description: >
  Use when: checking if .env file is complete, comparing .env vs .env.example,
  debugging "missing environment variable" errors, onboarding a new developer,
  security audit of environment configuration.
  Triggers: "env ontbreekt", "environment variabele", ".env controleren", "onboarding",
  "missing env", "omgevingsvariabele", "secrets controleren", "env audit".
---

# Env Audit Skill — VorstersNV

## Doel

Valideer de volledigheid en correctheid van het `.env` bestand ten opzichte van `.env.example`.
Identificeer ontbrekende variabelen, geef uitleg wat ze doen, en check of secrets niet in code staan.

---

## Stap 1: Lees Referentie en Actueel .env

```python
# Lees altijd in deze volgorde:
1. .env.example    ← de referentie (wat MOET aanwezig zijn)
2. .env            ← de actuele configuratie (wat IS aanwezig)
```

Als `.env.example` ontbreekt: **stop en meld dit** — het project mist zijn configuratiereferentie.
Als `.env` ontbreekt: **genereer instructies** om het aan te maken op basis van `.env.example`.

---

## Stap 2: Vergelijk en Categoriseer

Vergelijk beide bestanden en categoriseer elke variabele:

| Status | Omschrijving |
|--------|-------------|
| ✅ Aanwezig | Variabele staat in `.env` met niet-lege waarde |
| ⚠️ Leeg | Variabele aanwezig maar zonder waarde (`KEY=`) |
| ❌ Ontbreekt | Variabele staat in `.env.example` maar niet in `.env` |
| 🔒 Extra | Variabele in `.env` maar NIET in `.env.example` (potentieel ongedocumenteerd) |

---

## Stap 3: Kritieke Variabelen Check

De volgende variabelen zijn **business-kritiek** — rapporteer ze altijd expliciet:

| Variabele | Beschrijving | Impact als ontbreekt |
|-----------|-------------|---------------------|
| `DATABASE_URL` | PostgreSQL verbindingsstring | API start niet op |
| `MOLLIE_API_KEY` | Mollie betaaldienst sleutel | Geen betalingen mogelijk |
| `WEBHOOK_SECRET` | Handtekening-verificatie Mollie webhooks | Webhooks worden genegeerd |
| `NEXTAUTH_SECRET` | Next.js sessie encryptie | Frontend auth werkt niet |
| `NEXTAUTH_URL` | Frontend base URL voor auth callbacks | Login-redirects falen |
| `REDIS_URL` | Redis cache verbinding | API degraded (geen caching) |
| `KEYCLOAK_CLIENT_SECRET` | Keycloak OAuth2 secret | Admin login werkt niet |
| `OLLAMA_BASE_URL` | Ollama AI server URL | Alle AI agents offline |
| `SECRET_KEY` | FastAPI JWT signing key | Auth tokens invalide |

---

## Stap 4: Security Check — Secrets in Code

Scan de codebase op hardcoded secrets:

```bash
# Zoek patronen die op secrets lijken
grep -r "MOLLIE_API_KEY\s*=" api/ --include="*.py"
grep -r "sk_live_\|sk_test_\|live_\|test_" . --include="*.py" --include="*.ts"
grep -r "password\s*=\s*[\"'][^$]" . --include="*.py"
grep -r "SECRET.*=.*[\"'][a-zA-Z0-9]{16,}" . --include="*.py"
```

**Rode vlag patronen:**
- Mollie keys: `live_...` of `test_...` hardcoded in code
- Database wachtwoord direct in connection string
- JWT secret als variabele in code (niet via `os.getenv()`)

---

## Stap 5: Rapport Genereren

### Format

```
╔══════════════════════════════════════════════════════╗
║  ENV AUDIT  ·  VorstersNV                            ║
╚══════════════════════════════════════════════════════╝

📊 Samenvatting
  Totaal in .env.example:  [N] variabelen
  ✅ Aanwezig:             [N] variabelen
  ⚠️  Leeg:               [N] variabelen
  ❌ Ontbreekt:            [N] variabelen

────────────────────────────────────────────────────────

🚨 KRITIEKE ONTBREKENDE VARIABELEN
  [Lijst met naam, beschrijving, en wat er misgaat]

⚠️  LEGE VARIABELEN
  [Lijst met naam en standaardwaarde uit .env.example]

🔒 NIET-GEDOCUMENTEERDE VARIABELEN
  [Variabelen in .env maar niet in .env.example]

────────────────────────────────────────────────────────

🔍 SECURITY CHECK
  [Bevindingen hardcoded secrets — of "Geen hardcoded secrets gevonden"]

────────────────────────────────────────────────────────

📋 ACTIES VEREIST
  [ ] [Actie 1]
  [ ] [Actie 2]
```

---

## Veelvoorkomende Issues en Oplossingen

### DATABASE_URL formaat

```bash
# PostgreSQL (productie/dev)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vorsternv

# SQLite (tests)
DATABASE_URL=sqlite+aiosqlite:///./test.db
```

### MOLLIE_API_KEY

```bash
# Test (gratis, geen echte betalingen)
MOLLIE_API_KEY=test_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Live (echte betalingen — NOOIT in .env.example committen!)
MOLLIE_API_KEY=live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### NEXTAUTH_SECRET genereren

```bash
# Genereer een veilig secret
openssl rand -base64 32
# Of via Node.js:
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```
