---
mode: agent
description: Voer een volledige security audit uit op geselecteerde code of een module van VorstersNV. Controleert op OWASP Top 10, HMAC-verificatie, SQL-injectie en hardcoded secrets.
---

# Security Audit

Voer een grondige security audit uit op de geselecteerde code of module.

## Audit Checklist

### 1. Authenticatie & Autorisatie
- [ ] Zijn alle endpoints beveiligd die dat vereisen?
- [ ] Worden JWT-tokens correct geverifieerd (expiry, signature)?
- [ ] Heeft elke rol alleen toegang tot zijn eigen data?
- [ ] Geen hardcoded credentials of API-keys in code?

### 2. Input Validatie
- [ ] Alle input gevalideerd via Pydantic (FastAPI) of Zod (Next.js)?
- [ ] Geen directe SQL-string-concatenatie (gebruik altijd parameterized queries)?
- [ ] Bestandsuploads: type-check, grootte-limit, geen executable extensies?
- [ ] Path traversal niet mogelijk in file-operaties?

### 3. Webhook Beveiliging
- [ ] HMAC-SHA256 verificatie aanwezig en correct?
- [ ] Wordt `hmac.compare_digest()` gebruikt (niet `==`)?
- [ ] Webhook endpoints returnen 200 ook bij ongeldige signature? (timing attack preventie)

### 4. OWASP Top 10 Quick Check
- [ ] **A01 Broken Access Control**: Autorisatiecontroles per endpoint?
- [ ] **A02 Cryptographic Failures**: Geen MD5/SHA1 voor wachtwoorden?
- [ ] **A03 Injection**: Alle DB-queries via ORM of geparametriseerd?
- [ ] **A05 Security Misconfiguration**: Debug-mode uit in productie?
- [ ] **A07 Auth Failures**: Rate limiting op login endpoint?
- [ ] **A09 Logging Failures**: Security events gelogd (login, access denied)?

### 5. VorstersNV Specifiek
- [ ] Mollie webhook: `X-Mollie-Signature` header gecontroleerd?
- [ ] Ollama agent: geen user-input direct in system prompt (prompt injection)?
- [ ] Admin routes: Keycloak rol `admin` vereist?
- [ ] CORS: alleen VorstersNV origins toegestaan in productie?

## Rapportage Formaat

Voor elk gevonden probleem:
```
[SEVERITY: KRITIEK/HOOG/MEDIUM/LAAG]
Locatie: <bestand>:<regel>
Probleem: <beschrijving>
Bewijs: <code snippet>
Fix: <concrete aanpassing>
```

## Auto-fix Instructies
Na de audit: geef voor elk KRITIEK/HOOG probleem direct de gecorrigeerde code.
Geef implementatie-instructies aan `@developer` voor complexere fixes.
