# Git Commit Conventies — VorstersNV

## Taal — VERPLICHT

**Commit messages zijn Nederlandstalig.** Alleen technische termen (SQL, API, etc.) mogen Engels blijven.

## Format — VERPLICHT

```
<type>(<scope>): <beschrijving>

[optionele body — max 72 tekens per regel]
```

- Max 72 tekens voor de onderwerpregel
- Imperativusvorm: "voeg toe" niet "toegevoegd"
- Geen punt aan het einde

## Types — VERPLICHT

| Type | Wanneer |
|------|---------|
| `feat` | Nieuwe functionaliteit |
| `fix` | Bug repareren |
| `docs` | Alleen documentatie |
| `refactor` | Code herstructureren (geen bugfix, geen feature) |
| `test` | Tests toevoegen of aanpassen |
| `perf` | Performance verbetering |
| `ci` | CI/CD pipeline aanpassen |
| `chore` | Afhankelijkheden bijwerken, build scripts |

## Scopes — AANBEVOLEN

| Scope | Beschrijving |
|-------|-------------|
| `api` | FastAPI backend |
| `frontend` | Next.js frontend |
| `db` | Database / Alembic |
| `agents` | Ollama agents / prompts |
| `mollie` | Betalingsintegratie |
| `auth` | Keycloak / NextAuth |
| `docker` | Containerisatie |
| `ci` | GitHub Actions |

## Voorbeelden

```bash
# GOED
feat(api): voeg productaanbevelingen endpoint toe
fix(frontend): herstel winkelwagen-teller bij pagina-refresh
docs(agents): beschrijf klantenservice agent werking
refactor(db): extraheer order queries naar apart service bestand
test(api): voeg integratietests toe voor betalingsflow
perf(api): cache productlijst in Redis voor 5 minuten
feat(agents): voeg review analyzer agent toe met sentiment scoring
fix(mollie): herstel webhook handtekening verificatie

# SLECHT
update code            # te vaag
Fixed bug              # Engelstalig en geen type
added new feature      # Engelstalig en geen type prefix
feat: product          # te kort, geen scope
```

## Beveiliging — VERPLICHT

- **Nooit secrets committen** — API sleutels, wachtwoorden, `.env` bestanden
- **Nooit `Co-Authored-By` AI-attributie** toevoegen — commit auteur is de developer
- **Nooit force-push** op beschermde branches (`main`, `develop`)

---

## Branch Naamgeving — AANBEVOLEN

```bash
# Format: <type>/<korte-beschrijving>
# Altijd kebab-case, Nederlandstalige beschrijving toegestaan

# GOED
feat/product-aanbevelingen
fix/winkelwagen-teller
refactor/order-service
docs/api-documentatie
test/betaling-flow

# SLECHT
feature_new          # underscore, geen beschrijving
Fix-Bug              # hoofdletter, te vaag
mijn-branch          # geen type prefix
```

---

## Commit Body — AANBEVOLEN bij complexe wijzigingen

```bash
# Kort subject (imperativus, max 72 chars)
feat(api): voeg retour-aanvraag endpoint toe

# Lege regel, dan body
Implementeert POST /api/orders/{id}/retour waarmee klanten
een retour kunnen aanvragen binnen de 14-dagenperiode.

Wijzigingen:
- OrderService.request_return() methode
- RETURN_REQUESTED status toegevoegd aan state machine
- E-mail notificatie naar klant en warehouse

Gerelateerd: #247

# Breaking changes altijd vermelden
feat(api)!: verander order status enums naar hoofdletters

BREAKING CHANGE: OrderStatus waarden zijn nu PENDING ipv pending.
Update alle clients die de /api/orders/ responses lezen.
```

---

## Anti-patronen

| ❌ SLECHT | ✅ GOED |
|-----------|--------|
| `update code` | `refactor(api): extraheer order queries naar repository` |
| `WIP` | `feat(frontend): voeg skeleton loader toe aan productgrid` (commit als klaar) |
| `Fixed bug` | `fix(mollie): herstel webhook handtekening verificatie` |
| `added new feature` | `feat(agents): voeg product aanbevelingen agent toe` |
| `changes` | `chore(deps): upgrade FastAPI van 0.109 naar 0.111` |
| Commit met leeg subject | Altijd beschrijvend subject verplicht |
| Meerdere ongerelateerde fixes in één commit | Eén commit per logische wijziging |

```bash
# ❌ SLECHT — alles in één commit
git add .
git commit -m "update"

# ✅ GOED — atomaire commits
git add api/services/order_service.py
git commit -m "feat(api): voeg order-annulering toe via OrderService"

git add tests/test_orders_api.py
git commit -m "test(api): voeg tests toe voor order-annulering endpoint"

git add .claude/skills/order-lifecycle/SKILL.md
git commit -m "docs(agents): update order-lifecycle skill met annulering flow"
```
