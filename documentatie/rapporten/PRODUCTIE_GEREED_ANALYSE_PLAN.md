# Productie Gereed Analyse Plan — phr-globalconfig

**Status:** Lopend
**Scope:** phr-globalconfig-develop (frontend + backend BFF + core)

---

## Sectie 10 — Backend Security Audit

**Datum:** 2025-07-17
**Auditrapport:** [`documentatie/BACKEND_SECURITY_AUDIT.md`](./BACKEND_SECURITY_AUDIT.md)

### Verdict

```
🔴 BLOCKERS PRESENT — NIET PRODUCTIE-KLAAR
```

### Kritieke Blokkerende Bevindingen

| # | Bevinding | Risico | Oplossing vereist |
|---|-----------|--------|-------------------|
| F1 | **Geen method-level autorisatie** op alle 30+ endpoints (8 controllers) — elke geverifieerde gebruiker heeft volledige toegang | 🔴 HIGH | `@FgaPermissionCheck` implementeren per endpoint |
| F2 | **Wildcard CORS** `@CrossOrigin(origins = "*")` op alle 8 controllers | 🔴 HIGH | Verwijderen + centrale CORS-config met expliciete origins |
| F7 | **Actuator legt secrets bloot** via `show-values=ALWAYS` | 🟠 MEDIUM | `NEVER` instellen voor productie |

### Overige Bevindingen (niet-blokkerend)

| # | Bevinding | Risico |
|---|-----------|--------|
| F3 | Geen fallback/circuit-breaker op `GlobalconfigCoreClient` | 🟠 MEDIUM |
| F4 | Geen fallback op `WcsClient`; `wcs.url` is leeg | 🟠 MEDIUM |
| F5 | `@Valid` ontbreekt op 16 `@RequestBody` parameters | 🟠 MEDIUM |
| F6 | Bean Validation constraints ontbreken in 10+ command-DTO's | 🟠 MEDIUM |
| F8 | X-Frame-Options en HSTS niet geconfigureerd | 🟡 LOW |

### Positieve Bevindingen

- ✅ `anyRequest().authenticated()` — globale JWT-authenticatie aanwezig
- ✅ Content-Security-Policy geconfigureerd (`default-src 'none'`)
- ✅ Stateless sessies (geen sessie-gebaseerde aanvallen mogelijk)
- ✅ JWT-token wordt correct doorgestuurd naar core via `AuthRequestInterceptor`
- ✅ Custom `ErrorDecoderImpl` voor Feign HTTP-foutverwerking

### Aanbevolen Acties (geprioriteerd)

1. 🔴 **Sprint 1 — Blokkerend:** FGA-checks implementeren + CORS beperken + Actuator beveiligen
2. 🟠 **Sprint 2 — Vóór go-live:** @Valid toevoegen + DTO-constraints + Feign fallbacks
3. 🟡 **Backlog:** Security headers aanvullen (X-Frame-Options, HSTS)

### Conclusie

De `phr-globalconfig-develop` backend functioneert correct als BFF-proxy naar de core backend, maar ontbeert **alle method-level autorisatielagen**. Dit is een fundamenteel beveiligingsgat in een systeem dat gevoelige HR-loonschaaldata beheert. Productie-deployment is geblokkeerd totdat F1 en F2 opgelost zijn.

---

*Volledig auditrapport: [`BACKEND_SECURITY_AUDIT.md`](./BACKEND_SECURITY_AUDIT.md)*
