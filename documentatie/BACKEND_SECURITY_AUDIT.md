# Backend Security Audit — phr-globalconfig-develop

**Datum:** 2025-07-17
**Auditor:** GitHub Copilot (senior security analysis)
**Stack:** Spring Boot 3.4.13 · Java 21 · Feign clients · MariaDB/Liquibase (core)
**Scope:** `C:\Users\kvo\Desktop\phr-globalconfig-develop\backend`

---

## 1. Executive Summary

De `phr-globalconfig-develop` backend is een BFF (Backend-for-Frontend) die inkomende REST-aanvragen doorstuurt naar de `globalconfig-core` backend via Feign-clients. De globale `anyRequest().authenticated()` guard vereist geldige JWT-authenticatie, maar er is **nul method-level autorisatie** geïmplementeerd via `@FgaPermissionCheck` of `@PreAuthorize`. Elke geverifieerde gebruiker kan daardoor alle 30+ endpoints aanroepen, ongeacht zijn rechten. Twee aanvullende productieblokkerende bevindingen zijn: wildcard CORS op alle controllers en ontbrekende Bean Validation op de meeste request-body DTO's.

---

## 2. Risicomatrix

| # | Categorie | Bevinding | Risico |
|---|-----------|-----------|--------|
| F1 | FGA Coverage | Geen method-level autorisatie op 30+ endpoints | 🔴 HIGH |
| F2 | CORS | `@CrossOrigin(origins = "*")` op alle 8 controllers | 🔴 HIGH |
| F3 | Feign Resilience | Geen fallback/circuit-breaker op GlobalconfigCoreClient | 🟠 MEDIUM |
| F4 | Feign Resilience | Geen fallback/circuit-breaker op WcsClient | 🟠 MEDIUM |
| F5 | Input Validation | Ontbrekende `@Valid` op 16 `@RequestBody` parameters | 🟠 MEDIUM |
| F6 | Input Validation | Ontbrekende Bean Validation constraints in 10+ DTO's | 🟠 MEDIUM |
| F7 | Actuator | `show-values=ALWAYS` legt config/env-waarden bloot | 🟠 MEDIUM |
| F8 | Security Headers | X-Frame-Options en HSTS niet expliciet geconfigureerd | 🟡 LOW |
| F9 | CSRF | CSRF uitgeschakeld (acceptabel voor stateless JWT) | ℹ️ INFO |
| F10 | Liquibase | Geen migratiebestanden in BFF (verwacht, core beheert DB) | ℹ️ INFO |

---

## 3. Bevindingen per Categorie

---

### 3.1 FGA Security Coverage 🔴 HIGH

#### F1 — Volledige afwezigheid van method-level autorisatie

**Beschrijving:**
Geen enkele `@RestController` bevat een `@FgaPermissionCheck`, `@PreAuthorize`, `@Secured`, of vergelijkbare method-level autorisatie-annotatie op klasse- of methodeniveau. De `SecurityConfiguration` beschermt enkel via `anyRequest().authenticated()`, wat betekent dat elke geldige JWT-houder onbeperkt toegang heeft tot alle muterende endpoints (POST, PUT, DELETE).

**Getroffen controllers en endpoints (alle onbeschermd):**

| Controller | Bestand | Endpoints |
|---|---|---|
| `AttractionBonusApi` | `attractionbonus/AttractionBonusApi.java:27-58` | GET /attraction-bonus/history, PUT /attraction-bonus/{id}/periods/{periodId}, PUT /attraction-bonus/{id}/periods/{periodId}/assimilation, POST /attraction-bonus/period/{periodId}/assimilation, POST /attraction-bonus, GET /attraction-bonus/{id}/revisions |
| `MappingApi` | `mapping/MappingApi.java:35-124` | GET /mappings/findAll/{id}, GET /mappings/{id}/periods/{periodId}, GET /mapping-values/{periodId}/children, POST /mappings/{id}/periods/{periodId}, PUT /mappings/{id}/periods/{periodId}, DELETE /mappings/{id}/periods/{periodId}, GET /mapping-applications, GET /mappings/{id}/revisions, POST /mappings/{periodId}/child-values, PUT /mappings/{periodId}/child-values/{childValueId}, DELETE /mappings/{periodId}/child-values/{childValueId}, GET /mappings/history/most-current |
| `ScaleApi` | `scale/ScaleApi.java:39-146` | POST /scales, GET /scales, GET /scales/{periodId}, GET /scales/history/{id}, GET /scales/{id}/periods/{periodId}, GET /scales/history/most-current, PUT /scales/{id}/periods/{periodId}, DELETE /scales/{periodId}, POST /scales/{scaleId}/steps, PUT /scales/{scalePeriodId}/steps/{stepId}, DELETE /scales/{scalePeriodId}/steps/{stepId}, POST /scales/{id}/periods/{periodId} |
| `ScaleAuditApi` | `scale/ScaleAuditApi.java:27-29` | GET /scales/revisions |
| `ScaleGroupApi` | `scale/group/ScaleGroupApi.java:37-144` | POST /scale-groups, GET /scale-groups, GET /scale-groups/{id}, GET /scale-groups/{id}/periods/{periodId}, GET /scale-groups/history/most-current, PUT /scale-groups/{id}/periods/{periodId}, POST /scale-groups/{id}/scales/{scaleId}, PUT /scale-groups/{id}/scales/{scaleId}, DELETE /scale-groups/{id}/scales/{scaleId}, DELETE /scale-groups/{periodId}, POST /scale-groups/{id}/periods/{periodId} |
| `ScaleTypeApi` | `scale/type/ScaleTypeApi.java:36-73` | POST /scale-types, GET /scale-types, PUT /scale-types/{id}, DELETE /scale-types/{id} |
| `ScaleTypeAuditApi` | `scale/type/ScaleTypeAuditApi.java:28-31` | GET /scale-types/revisions |
| `PermissionsApi` | `finegrainedsecurity/PermissionsApi.java:29-36` | GET /permissions |

**Aanbeveling:**
Voeg `@FgaPermissionCheck` (of `@PreAuthorize`) toe op klasse- of methodeniveau voor alle controllers. Minimaal:

```java
// Voorbeeld ScaleApi
@FgaPermissionCheck("scale:read")
@GetMapping("/scales")
public List<Scale> find(...) { ... }

@FgaPermissionCheck("scale:write")
@PostMapping("/scales")
public Scale createScale(@RequestBody ScaleCreateCommand cmd) { ... }

@FgaPermissionCheck("scale:delete")
@DeleteMapping("/scales/{periodId}")
public void deleteByPeriodId(@PathVariable String periodId) { ... }
```

Of op klasseniveau (grove granulariteit):
```java
@FgaPermissionCheck("scale:admin")
@RestController
public class ScaleApi { ... }
```

---

### 3.2 CORS Configuratie 🔴 HIGH

#### F2 — Wildcard CORS op alle controllers

**Beschrijving:**
Alle 8 `@RestController`-klassen zijn geannoteerd met `@CrossOrigin(origins = "*")`. Dit staat verzoeken toe van elke willekeurige oorsprong, inclusief kwaadaardige websites. Dit is een productieblokkerende misconfiguratie die CSRF-achtige aanvallen via cross-origin requests faciliteert, ook in stateless JWT-scenarios.

**Getroffen bestanden:**

| Bestand | Regel |
|---|---|
| `attractionbonus/AttractionBonusApi.java` | 24 |
| `mapping/MappingApi.java` | 30 |
| `scale/ScaleApi.java` | 29 |
| `scale/ScaleAuditApi.java` | 16 |
| `scale/group/ScaleGroupApi.java` | 27 |
| `scale/type/ScaleTypeApi.java` | 27 |
| `scale/type/ScaleTypeAuditApi.java` | 18 |
| `finegrainedsecurity/PermissionsApi.java` | 18 |

**Aanbeveling:**
Verwijder alle `@CrossOrigin(origins = "*")` annotaties van de controllers. Configureer CORS centraal in `SecurityConfiguration.java` met expliciete toegestane origins:

```java
// In SecurityConfiguration.filterChain():
.cors(cors -> cors.configurationSource(request -> {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of(
        "https://globalconfig.cipalschaubroeck.be",
        "https://acc-globalconfig.cipalschaubroeck.be"
    ));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
    config.setAllowedHeaders(List.of("Authorization", "Content-Type"));
    config.setAllowCredentials(true);
    return config;
}))
```

---

### 3.3 Feign Client Resilience 🟠 MEDIUM

#### F3 — GlobalconfigCoreClient zonder fallback of circuit-breaker

**Beschrijving:**
`GlobalconfigCoreClient` (50 methoden, alle productie-domeinoperaties) heeft geen `fallback`, `fallbackFactory` of Resilience4j `@CircuitBreaker`. Bij een storing van de core-backend propageren alle aanroepen direct als HTTP 500 naar de client. Er is een `ErrorDecoderImpl` die HTTP-foutresponsen vertaalt, maar netwerktimeouts en verbindingsproblemen worden niet opgevangen.

**Bestand:** `GlobalconfigCoreClient.java:50`
```java
@FeignClient(name = "GlobalconfigCoreClient", url = "${core.client.url}")
// ↑ Geen fallbackFactory = cascade failure bij core-backend uitval
public interface GlobalconfigCoreClient { ... }
```

**Aanbeveling:**
```java
@FeignClient(
    name = "GlobalconfigCoreClient",
    url = "${core.client.url}",
    fallbackFactory = GlobalconfigCoreClientFallbackFactory.class
)
public interface GlobalconfigCoreClient { ... }

@Component
public class GlobalconfigCoreClientFallbackFactory
        implements FallbackFactory<GlobalconfigCoreClient> {
    @Override
    public GlobalconfigCoreClient create(Throwable cause) {
        log.error("GlobalconfigCoreClient unavailable", cause);
        throw new ServiceUnavailableException("Core backend tijdelijk niet beschikbaar");
    }
}
```

Voeg ook timeoutconfiguratie toe in `application.properties`:
```properties
spring.cloud.openfeign.client.config.GlobalconfigCoreClient.connect-timeout=5000
spring.cloud.openfeign.client.config.GlobalconfigCoreClient.read-timeout=10000
```

#### F4 — WcsClient zonder fallback of circuit-breaker

**Beschrijving:**
`WcsClient` (WCS Fine-Grained Authorization service) heeft geen fallback. Als de WCS-service onbeschikbaar is, geeft `PermissionsApi.findAll()` een 500-fout terug. De `wcs.url` property is bovendien **leeg** in `application.properties:52`, wat aangeeft dat dit nooit correct geconfigureerd is.

**Bestand:** `WcsClient.java:7`
```java
@FeignClient(name = "WcsClient", url = "${wcs.url}")
// ↑ wcs.url is leeg in application.properties!
public interface WcsClient { ... }
```

**Bestand:** `application.properties:52`
```properties
wcs.url=   # ← LEEG — WcsClient zal altijd falen in deze configuratie
```

**Aanbeveling:**
1. Stel `wcs.url` in per deployment-profiel (local, acc, prod)
2. Voeg fallback toe die een lege lijst retourneert bij onbeschikbaarheid:
```java
@FeignClient(name = "WcsClient", url = "${wcs.url}", fallback = WcsClientFallback.class)
```

---

### 3.4 Input Validation 🟠 MEDIUM

#### F5 — Ontbrekende `@Valid` annotaties op `@RequestBody` parameters

**Beschrijving:**
Zelfs wanneer DTO's Bean Validation constraints bevatten (bijv. `ScaleUpdatePeriodCommand`), worden deze nooit geactiveerd omdat `@Valid` ontbreekt op de controller-parameter. Spring Boot valideert `@RequestBody` enkel als `@Valid` of `@Validated` aanwezig is.

**Getroffen endpoints:**

| Bestand | Regel | Methode | Ontbreekt |
|---|---|---|---|
| `attractionbonus/AttractionBonusApi.java` | 33 | `updatePeriod` | `@Valid` op `AttractionBonusUpdatePeriodCommand` |
| `attractionbonus/AttractionBonusApi.java` | 51 | `createConfig` | `@Valid` op `AttractionBonusCreateCommand` |
| `scale/ScaleApi.java` | 40 | `createScale` | `@Valid` op `ScaleCreateCommand` |
| `scale/ScaleApi.java` | 99 | `updatePeriod` | `@Valid` op `ScaleUpdatePeriodCommand` (DTO HÁS constraints maar @Valid ontbreekt) |
| `scale/ScaleApi.java` | 119 | `addStepToScale` | `@Valid` op `StepCreateCommand` |
| `scale/ScaleApi.java` | 128 | `updateStepFromScale` | `@Valid` op `StepUpdateCommand` |
| `scale/ScaleApi.java` | 143 | `createPeriod` | `@Valid` op `ScaleCreatePeriodCommand` |
| `scale/group/ScaleGroupApi.java` | 38 | `createScaleGroup` | `@Valid` op `ScaleGroupCreateCommand` |
| `scale/group/ScaleGroupApi.java` | 89 | `updatePeriod` | `@Valid` op `ScaleGroupUpdateCommand` |
| `scale/group/ScaleGroupApi.java` | 100 | `addScaleToGroup` | `@Valid` op `AddScaleToGroupCommand` |
| `scale/group/ScaleGroupApi.java` | 111 | `updateScaleFromGroup` | `@Valid` op `UpdateScaleFromGroupCommand` |
| `scale/group/ScaleGroupApi.java` | 142 | `createPeriod` | `@Valid` op `ScaleGroupCreatePeriodCommand` |
| `scale/type/ScaleTypeApi.java` | 37 | `createScaleType` | `@Valid` op `ScaleTypeCreateCommand` |
| `scale/type/ScaleTypeApi.java` | 61 | `update` | `@Valid` op `ScaleTypeUpdateCommand` |
| `mapping/MappingApi.java` | 87 | `addChildValueToScale` | `@Valid` op `ChildValueCreateCommand` |
| `mapping/MappingApi.java` | 102 | `updateChildValueInMapping` | `@Valid` op `ChildValueUpdateCommand` |

#### F6 — Ontbrekende Bean Validation constraints in DTO's

**Beschrijving:**
De meeste command-records bevatten enkel OpenAPI `@Schema`-annotaties voor documentatie. Deze hebben geen runtime-validatiefunctie. De volgende DTO's missen `@NotNull`, `@NotBlank`, `@Size`, `@Min`, `@Max` of equivalente constraints:

| DTO | Bestand | Constraints aanwezig |
|---|---|---|
| `AttractionBonusCreateCommand` | `attractionbonus/AttractionBonusCreateCommand.java` | ❌ Geen |
| `AttractionBonusUpdatePeriodCommand` | `attractionbonus/AttractionBonusUpdatePeriodCommand.java` | ❌ Geen |
| `ScaleCreateCommand` | `scale/ScaleCreateCommand.java` | ❌ Geen |
| `ScaleGroupCreateCommand` | `scale/group/ScaleGroupCreateCommand.java` | ❌ Geen |
| `ScaleGroupUpdateCommand` | `scale/group/ScaleGroupUpdateCommand.java` | ❌ Geen |
| `ScaleTypeCreateCommand` | `scale/type/ScaleTypeCreateCommand.java` | ❌ Geen |
| `ScaleTypeUpdateCommand` | `scale/type/ScaleTypeUpdateCommand.java` | ❌ Geen |
| `ChildValueCreateCommand` | `mapping/childvalue/ChildValueCreateCommand.java` | ❌ Geen |
| `ChildValueUpdateCommand` | `mapping/childvalue/ChildValueUpdateCommand.java` | ❌ Geen |
| `StepCreateCommand` | `scale/step/StepCreateCommand.java` | ❌ Geen |
| `ScaleUpdatePeriodCommand` | `scale/ScaleUpdatePeriodCommand.java` | ✅ `@NotNull`, `@Size` aanwezig |
| `AttractionBonusAssimilationCreateCommand` | `attractionbonus/AttractionBonusAssimilationCreateCommand.java` | ✅ `@NotNull`, `@DecimalMin`, `@DecimalMax` aanwezig |

**Aanbeveling (voorbeeld voor `ScaleCreateCommand`):**
```java
public record ScaleCreateCommand(
    @NotNull(message = "validityPeriod is verplicht")
    ValidityPeriod validityPeriod,

    @NotBlank(message = "name is verplicht")
    @Size(max = 50, message = "name mag maximaal 50 tekens bevatten")
    String name,

    @NotBlank(message = "type is verplicht")
    @Size(min = 36, max = 36, message = "type moet een UUID zijn van 36 tekens")
    String type,

    Long capeloCode,  // optioneel

    @NotNull(message = "salaryRange is verplicht")
    SalaryRange salaryRange
) {}
```

En op de controller:
```java
@PostMapping("/scales")
public Scale createScale(@Valid @RequestBody ScaleCreateCommand cmd) { ... }
```

---

### 3.5 Security Headers 🟡 LOW / ℹ️ INFO

#### F7 — Actuator legt configuratiewaarden bloot (MEDIUM)

**Beschrijving:**
`application.properties` configureert drie actuator-endpoints om alle waarden altijd zichtbaar te maken. Dit includeert potentieel gevoelige informatie zoals database-credentials, JWT-secrets en API-sleutels.

**Bestand:** `application.properties:39-41`
```properties
management.endpoint.configprops.show-values=ALWAYS  # ← toont alle Spring properties
management.endpoint.env.show-values=ALWAYS          # ← toont alle omgevingsvariabelen
management.endpoint.quartz.show-values=ALWAYS
```

**Aanbeveling:**
Verander naar `WHEN_AUTHORIZED` of `NEVER` voor productie:
```properties
management.endpoint.configprops.show-values=NEVER
management.endpoint.env.show-values=NEVER
management.endpoint.quartz.show-values=WHEN_AUTHORIZED
```

#### F8 — X-Frame-Options en HSTS niet geconfigureerd (LOW)

**Beschrijving:**
`SecurityConfiguration.java` stelt geen X-Frame-Options (clickjacking-bescherming) of HTTP Strict-Transport-Security (HSTS) headers in. Spring Security 6 voegt deze headers niet meer automatisch toe.

**Bestand:** `configuration/security/SecurityConfiguration.java:37-48`

**Aanbeveling:**
```java
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp.policyDirectives("default-src 'none'"))
    .frameOptions(frame -> frame.deny())
    .httpStrictTransportSecurity(hsts -> hsts
        .includeSubDomains(true)
        .maxAgeInSeconds(31536000)
    )
);
```

#### F9 — CSRF uitgeschakeld (INFO/ACCEPTABEL)

**Beschrijving:**
CSRF-bescherming is uitgeschakeld via `AbstractHttpConfigurer::disable`. Dit is standaardpraktijk voor stateless REST-API's die JWT-authenticatie gebruiken (geen sessiecookies). **Geen actie vereist**, maar documenteer dit in de security baseline.

**Bestand:** `configuration/security/SecurityConfiguration.java:38`

#### Positieve bevindingen:

| Bevinding | Status |
|---|---|
| Content-Security-Policy `"default-src 'none'"` | ✅ Goed geconfigureerd |
| Sessies: `SessionCreationPolicy.STATELESS` | ✅ Correct |
| JWT via `oauth2ResourceServer` | ✅ Correct |
| Swagger-UI uitgesloten van auth in dev | ✅ Correct (niet voor prod) |
| `AuthRequestInterceptor` stuurt JWT door naar core | ✅ Correct |
| Toegangslog geconfigureerd | ✅ Aanwezig |

---

### 3.6 Liquibase Migraties ℹ️ INFO (Niet van Toepassing)

**Beschrijving:**
De BFF-backend bevat geen `db/changelog`-directory en geen Liquibase-configuratie. Dit is **verwacht en correct**: als BFF-gateway beheert deze service geen eigen database. De databasemigraties voor scale, mapping, attractionbonus, finegrainedsecurity en configuration zijn de verantwoordelijkheid van de `phr-globalconfig-core` backend.

**Geen actie vereist.**

---

## 4. Samenvatting per Controller

| Controller | Auth-check | CORS | @Valid | Risico |
|---|---|---|---|---|
| `AttractionBonusApi` | 🔴 Geen | 🔴 Wildcard | 🟠 Gedeeltelijk | 🔴 HIGH |
| `MappingApi` | 🔴 Geen | 🔴 Wildcard | 🟠 Gedeeltelijk | 🔴 HIGH |
| `ScaleApi` | 🔴 Geen | 🔴 Wildcard | 🔴 Ontbreekt | 🔴 HIGH |
| `ScaleAuditApi` | 🔴 Geen | 🔴 Wildcard | ✅ N/A (geen body) | 🔴 HIGH |
| `ScaleGroupApi` | 🔴 Geen | 🔴 Wildcard | 🔴 Ontbreekt | 🔴 HIGH |
| `ScaleTypeApi` | 🔴 Geen | 🔴 Wildcard | 🔴 Ontbreekt | 🔴 HIGH |
| `ScaleTypeAuditApi` | 🔴 Geen | 🔴 Wildcard | ✅ N/A (geen body) | 🔴 HIGH |
| `PermissionsApi` | 🔴 Geen | 🔴 Wildcard | ✅ N/A (geen body) | 🔴 HIGH |

---

## 5. Aanbevolen Remediatievolgorde

### Blokkerend voor Productie (Sprint 1)
1. **[F1]** Implementeer `@FgaPermissionCheck` op alle controllers — alle 30+ endpoints
2. **[F2]** Verwijder `@CrossOrigin(origins = "*")` van alle controllers; configureer CORS centraal met expliciete origins
3. **[F7]** Zet `management.endpoint.*.show-values=NEVER` voor productie

### Vóór Go-Live (Sprint 2)
4. **[F5+F6]** Voeg `@Valid` toe aan alle `@RequestBody` parameters; voeg Bean Validation constraints toe aan alle command-DTO's
5. **[F3]** Voeg fallbackFactory en timeout-config toe aan `GlobalconfigCoreClient`
6. **[F4]** Voeg fallback toe aan `WcsClient`; configureer `wcs.url` per profiel

### Nice-to-Have (Backlog)
7. **[F8]** Voeg X-Frame-Options en HSTS toe aan `SecurityConfiguration`

---

## 6. Overall Verdict

```
╔══════════════════════════════════════════╗
║  VERDICT: 🔴 BLOCKERS PRESENT           ║
║                                          ║
║  Niet productie-klaar:                   ║
║  • F1: Geen method-level autorisatie     ║
║  • F2: Wildcard CORS op alle controllers ║
║  • F7: Actuator legt secrets bloot       ║
╚══════════════════════════════════════════╝
```

De backend is functioneel correct als BFF-proxy maar **mist fundamentele autorisatielagen**. Met de huidige staat kan elke geverifieerde gebruiker (ook met minimale rechten) alle data ophalen, aanpassen en verwijderen. Dit is een kritisch beveiligingsgebrek voor een loonschaal-configuratiesysteem met gevoelige HR-data.

---

*Audit gegenereerd op basis van statische code-analyse. Geen penetratietest of runtime-analyse uitgevoerd.*
