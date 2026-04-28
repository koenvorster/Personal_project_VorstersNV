# WCS — Codebase Analyse
**Klant:** Cipal Schaubroeck NV  
**Project:** Web Client Service (WCS)  
**Analist:** VorstersNV Consultancy  
**Datum:** 2025  
**Status:** Definitief

---

## Inhoudsopgave
1. [Executive Summary](#1-executive-summary)
2. [Technologie Stack](#2-technologie-stack)
3. [Architectuuroverzicht](#3-architectuuroverzicht)
4. [Moduleverantwoordelijkheden](#4-moduleverantwoordelijkheden)
5. [Domeinmodel & Business Rules](#5-domeinmodel--business-rules)
6. [Lifecycle State Machines](#6-lifecycle-state-machines)
7. [API Overzicht](#7-api-overzicht)
8. [Beveiligingsarchitectuur](#8-beveiligingsarchitectuur)
9. [Frontend Analyse](#9-frontend-analyse)
10. [Kwaliteitsanalyse](#10-kwaliteitsanalyse)
11. [Risico-inventaris](#11-risico-inventaris)
12. [Aanbevelingen](#12-aanbevelingen)
13. [Conclusie](#13-conclusie)
14. [Glossarium](#14-glossarium)

---

## 1. Executive Summary

**WCS (Web Client Service)** is een enterprise **Identity & Access Management (IAM) beheerplatform** ontwikkeld door Cipal Schaubroeck NV voor Belgische overheidsinstanties. Het systeem fungeert als de beheerslaag bovenop Keycloak en stelt beheerders in staat om gebruikers, rollen, groepen, tenants en OIDC-clients te beheren — waarna alle wijzigingen automatisch worden gesynchroniseerd naar de Keycloak-instantie.

### Kernfuncties
- **Multi-tenant gebruikersbeheer**: Gemeenten, OCMW's en overheidsorganisaties (tenants) beheren hun eigen medewerkers
- **Keycloak synchronisatie**: Alle IAM-data in WCS wordt bidirectioneel gesynchroniseerd naar Keycloak
- **LIMA-integratie**: Koppeling met externe HR/payrollsystemen voor automatische gebruikersaanmaak en -beheer
- **Self-service portaal**: Medewerkers kunnen via het Angular-portaal hun applicaties, bookmarks en contactpersonen bekijken
- **WQM-module**: Rapportage en autorisatiebeheer voor een specifieke werknemersauthenticatiemodule
- **Payflip-integratie**: Fietsleasingbeheer via externe Payflip API

### Schaalgrootte
- **Backend**: ~15 Maven-modules, 200+ REST-endpoints, 100+ domeinklassen
- **Frontend**: Angular single-page application met 2 functionele modules
- **Omgevingen**: dev, test, demo, int (integratie), poc, productie

---

## 2. Technologie Stack

### Backend

| Component | Technologie | Versie | Toelichting |
|-----------|-------------|--------|-------------|
| Taal | Java | 17 | LTS release, records en sealed classes beschikbaar |
| Framework | Spring Boot | 3.5.13 | Meest recente versie op analysedatum |
| Database primair | MariaDB | Driver 3.5.8 | Productiedatabase |
| Database secundair | IBM Informix | Driver 15.0.1.1 | Externe databronintegratie (LIMA) |
| ORM | Spring Data JPA / Hibernate | — | `ddl-auto=validate` (schema via Liquibase) |
| Schema migraties | Liquibase | — | Java-based changesets in `wcs-db` module |
| Authenticatie | Keycloak | 26.6.0 | `keycloak-core` + `keycloak-adapter-spi` |
| Bean mapping | MapStruct | 1.6.3 | Strict: `unmappedTargetPolicy=ERROR` |
| API documentatie | SpringDoc OpenAPI | 2.8.17 | Uitgeschakeld in productie |
| Excel export | Apache POI | 5.5.1 | Rapportage exports |
| CSV export | Apache Commons CSV | 1.14.1 | WQM-rapporten |
| Test-stubs | WireMock | 3.13.2 | Externe service mocking |
| Test DB | H2 | — | In-memory integratietests |
| Code kwaliteit | SpotBugs, JaCoCo, SonarQube | — | CI/CD integratie |
| Build | Maven multi-module | — | Versioning via plugin |

### Frontend

| Component | Technologie | Versie | Toelichting |
|-----------|-------------|--------|-------------|
| Framework | Angular | 21.2.8 | Zeer recent, stable |
| UI componenten | PrimeNG | 21.1.5 | Enterprise UI bibliotheek |
| CSS framework | Tailwind CSS | 4 | Utility-first styling |
| Authenticatie | keycloak-angular | 21.0.0 | + eigen `@cipalschaubroeck/phr-ng-keycloak` |
| Internationalisatie | @ngx-translate/core | 17 | Multi-taal ondersteuning |
| State management | RxJS BehaviorSubject | — | Eenvoudige custom store (geen NgRx) |
| Linting | angular-eslint + typescript-eslint | 21 / 8 | Strikte typechecking |
| UI Design System | @cipalschaubroeck/jangosquare-* | — | Eigen Cipal Schaubroeck component lib |

---

## 3. Architectuuroverzicht

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNE SYSTEMEN                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  LIMA    │  │ Payflip  │  │  CoreHR  │  │ FAS (Federale Auth)│ │
│  │ (HR/pay) │  │ (fiets)  │  │ (payroll)│  │                    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────────────────┘ │
└───────┼─────────────┼─────────────┼────────────────────────────────┘
        │             │             │
┌───────▼─────────────▼─────────────▼────────────────────────────────┐
│                      WCS BACKEND (Spring Boot)                      │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     REST LAAG (wcs-rest)                      │  │
│  │  account | lima | management | portal | private | public | wqm│  │
│  └──────────────────────┬───────────────────────────────────────┘  │
│                          │                                           │
│  ┌──────────────────────▼───────────────────────────────────────┐  │
│  │                   SERVICE LAAG (wcs-service)                  │  │
│  │  UserService | TenantService | KeycloakSyncService | MailServ │  │
│  │  + wcs-account-service | wcs-lima-service | wcs-wqm-service   │  │
│  │  + wcs-management-service | wcs-portal-service                │  │
│  └──────────┬────────────────────────────────┬───────────────────┘  │
│             │                                │                       │
│  ┌──────────▼──────────┐          ┌──────────▼──────────────────┐  │
│  │  PERSISTENCE LAAG   │          │  KEYCLOAK SERVICE LAAG      │  │
│  │  (wcs-persistence)  │          │  (wcs-keycloak-service)     │  │
│  │  Spring Data JPA    │          │  Keycloak Admin REST API    │  │
│  └──────────┬──────────┘          └──────────┬──────────────────┘  │
│             │                                │                       │
│  ┌──────────▼──────────┐          ┌──────────▼──────────────────┐  │
│  │  DOMEIN LAAG        │          │  KEYCLOAK SERVER             │  │
│  │  (wcs-domain)       │          │  (Keycloak 26.6.0)          │  │
│  │  Entiteiten, Enums  │          └─────────────────────────────┘  │
│  │  Business Rules     │                                            │
│  └──────────┬──────────┘                                            │
│             │                                                        │
│  ┌──────────▼──────────┐                                            │
│  │  DATABASE           │                                            │
│  │  MariaDB (prod)     │                                            │
│  │  Liquibase migraties│                                            │
│  └─────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────┘
        ▲
        │ REST API (/api/portal/...)
        │
┌───────┴─────────────────────────────────────────────────────────────┐
│                  ANGULAR FRONTEND (wcs-portal)                      │
│  Portaal voor medewerkers: applicaties, bookmarks, dossierbeheerder │
│  Keycloak SSO authenticatie                                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Lagenprincipes
- **Domeinlaag** (`wcs-domain`): Pure Java, **geen Spring-afhankelijkheden**. Bevat alle business rules als invarianten.
- **Persistentielaag** (`wcs-persistence`): Spring Data JPA repositories. Geen business logic.
- **Servicelaag**: Spring `@Service` beans. Coördineert business logic en persistentie.
- **REST-laag** (`wcs-rest`): Spring MVC controllers. Dunne laag: validatie + DTO-mapping via MapStruct.
- **Keycloak-servicelaag** (`wcs-keycloak-service`): Encapsuleert alle Keycloak Admin API calls.

---

## 4. Moduleverantwoordelijkheden

| Module | Verantwoordelijkheid | Afhankelijkheden |
|--------|---------------------|------------------|
| `wcs-domain` | Entiteiten, enums, exceptions, business rules. Geen Spring. | Alleen Java std lib + JPA annotations |
| `wcs-db` | Liquibase changesets (Java-based). Database schema beheer. | wcs-domain |
| `wcs-persistence` | Spring Data JPA repositories. Query-methoden. | wcs-domain |
| `wcs-service` | Kernbusiness logica: gebruikersbeheer, tenantbeheer, mail, audit, Keycloak-sync coördinatie | wcs-domain, wcs-persistence, wcs-keycloak-service |
| `wcs-keycloak-service` | Directe Keycloak Admin REST API integratie. Gebruikers, groepen, rollen, clients aanmaken/bijwerken in Keycloak. | wcs-domain |
| `wcs-account-service` | Account self-service: 2FA beheer, gebruikersdetails bijwerken | wcs-service |
| `wcs-management-service` | Admin/beheers-UI services: tenant aanmaken, gebruikersbeheer, bulkoperaties | wcs-service |
| `wcs-lima-service` | LIMA-integratie: inkomende HR-data verwerken, gebruikers automatisch aanmaken/bijwerken | wcs-service |
| `wcs-portal-service` | Portaal-services: applicatie-overzicht, bookmarks ophalen | wcs-service |
| `wcs-wqm-service` | WQM (Werknemers Query Module): autorisatiecodes ophalen + CSV-rapporten genereren | wcs-service |
| `wcs-rest` (sub-modules) | REST controllers per domeincontext. DTO-klassen. MapStruct mappers. | Alle bovenstaande service-modules |
| `wcs-backend` | Spring Boot applicatie entry point. Configuratie, security, auto-configuratie. | Alle modules |

---

## 5. Domeinmodel & Business Rules

### Kernentiteiten

```
┌─────────────┐    N   ┌─────────────┐    N   ┌─────────────┐
│   Tenant    ├────────┤    User     ├────────┤    Role     │
│ (gemeente/  │        │ (medewerker)│        │ (functierol)│
│ organisatie)│        └──────┬──────┘        └─────────────┘
└──────┬──────┘               │
       │N                     │N
       │               ┌──────▼──────┐
┌──────▼──────┐         │UserAttribute│
│   Client    │         │(WQM codes,  │
│ (OIDC app)  │         │ extra data) │
└─────────────┘         └─────────────┘
```

### Business Rules Tabel

| Regel | Beschrijving | Code Locatie | Prioriteit |
|-------|-------------|--------------|------------|
| BR-001 | Een gebruiker kan alleen worden gekoppeld aan een tenant die actief is (niet REMOVED) | `User.java` | Hoog |
| BR-002 | SyncStatus-overgang: PREPARING → READY → OK; fout → DIRTY; actieve sync → BUSY | `SyncStatus.java` | Hoog |
| BR-003 | UserStatus-lifecycle: NEW → READY → OK; deactivatie → DISABLED; verwijdering → REMOVED | `UserStatus.java` | Hoog |
| BR-004 | Een tenant mag alleen bepaalde ClientTypes gebruiken op basis van zijn TenantType (CSPAYROLLHR, FSSC, SC, PROXY) | `Tenant.allowsToUseClient()` | Hoog |
| BR-005 | Rollen worden gecontroleerd via `@AuthorizeAction` annotaties — elke actie heeft een specifieke rol nodig | `Roles.java`, `Action.java` | Hoog |
| BR-006 | `User.isAllowedTo()` controleert of een gebruiker een specifieke actie mag uitvoeren op basis van zijn rollen en tenant | `User.java:114` | Hoog |
| BR-007 | MapStruct mapping met `unmappedTargetPolicy=ERROR` — elke nieuw entiteitsveld **moet** expliciet worden gemapt of geëxcludeerd | `pom.xml` (MapStruct config) | Middel |
| BR-008 | Swagger/OpenAPI is uitgeschakeld in productie (`springdoc.api-docs.enabled=false`) | `application-prod.properties` | Middel |
| BR-009 | WQM-rapporten bevatten alleen ACTIEVE gebruikers (UserStatus ≠ REMOVED en ≠ DISABLED) | `WqmReportServiceImpl.java` | Middel |
| BR-010 | WCS heeft twee speciale system-tenants: `testusers` en `cspayrollhr` (hardcoded URI's) | `WcsConstants.java` | Middel |
| BR-011 | Database schema wordt GEVALIDEERD bij opstart (`ddl-auto=validate`) — geen auto-create in productie | `application.properties` | Hoog |
| BR-012 | Keycloak-migratie kan via admin API (`/api/management/admin/migrate-to-keycloak`) worden getriggerd | `management-rest` | Laag |
| BR-013 | Payflip-integratie gebruikt Auth0 OAuth2 (afzonderlijke client credentials per omgeving) | `application.properties` | Middel |
| BR-014 | LIMA-integratie heeft aparte rollen: `ROLE_LIMA_API` (lezen) en `ROLE_LIMA_CMD` (schrijven/commandos) | `Roles.java` | Hoog |

### TenantType → ClientType mapping (BR-004 detail)
| TenantType | Toegestane ClientTypes |
|------------|----------------------|
| CSPAYROLLHR | PHR, MYHR, COREHR, WQM, ... |
| FSSC | Subset van bovenstaande |
| SC | Beperkte subset |
| PROXY | Proxy-specifieke clients |

---

## 6. Lifecycle State Machines

### UserStatus Lifecycle
```
          ┌─────────┐
          │   NEW   │  (gebruiker aangemaakt, nog niet gesynchroniseerd)
          └────┬────┘
               │ sync klaar
          ┌────▼────┐
          │  READY  │  (klaar, wacht op Keycloak sync)
          └────┬────┘
               │ sync succesvol
          ┌────▼────┐
     ┌────┤   OK    ├────┐
     │    └─────────┘    │
     │ deactiveer        │ verwijder
┌────▼────┐         ┌────▼────┐
│DISABLED │         │REMOVED  │
└─────────┘         └─────────┘
     │ reactiveer
     └──────────────► OK
```

### SyncStatus Lifecycle
```
         ┌───────────┐
         │ PREPARING │  (entity aangemaakt, sync nog niet gestart)
         └─────┬─────┘
               │ klaar voor sync
         ┌─────▼─────┐
         │   READY   │  (wacht op volgende sync-cycle)
         └─────┬─────┘
               │ sync gestart
    ┌──────────▼─────────┐
    │        BUSY        │  (sync actief bezig)
    └──────────┬─────────┘
          ┌────┴────┐
          │         │
    ┌─────▼────┐ ┌──▼──────┐
    │    OK    │ │  DIRTY  │  (fout tijdens sync → herpoging nodig)
    └──────────┘ └─────────┘
                      │ herpoging
                      └──────────► READY
```

---

## 7. API Overzicht

### REST Context Overzicht

| Context | Basispad | Doelgroep | Aantal endpoints (geschat) |
|---------|----------|-----------|---------------------------|
| Account | `/api/account/...` | Ingelogde gebruiker (self-service) | ~15 |
| LIMA | `/api/lima/...` + `/api/lima/v1/...` | LIMA-integratie systemen | ~25 |
| Management | `/api/management/...` | Beheerders (admin UI) | ~80 |
| Management Admin | `/api/management/admin/...` | Super-admin commando's | ~10 |
| Management Commands | `/api/management/commands/...` | Bulk operaties | ~10 |
| Management Providers | `/api/management/providers/...` | Lookup data (enums, lists) | ~20 |
| Portal | `/api/portal/...` | Angular portaal frontend | ~20 |
| Private | `/api/private/...` | Interne service-naar-service | ~10 |
| Public | `/api/public/...` | Publiek toegankelijk (geen auth) | ~5 |
| WQM | `/api/wqm/v1/...` | WQM-module (autorisatie + rapporten) | ~10 |

**Totaal: ~200+ endpoints**

### Geselecteerde Endpoints (Management — meest complex)

| Endpoint | Methode | Beschrijving |
|----------|---------|-------------|
| `/api/management/users` | GET | Gebruikerslijst met filtering |
| `/api/management/users/{id}` | GET / PUT | Gebruikersdetails lezen/bijwerken |
| `/api/management/users/{id}/roles` | GET / PUT | Rollen van gebruiker beheren |
| `/api/management/users/{id}/status` | PUT | Gebruikersstatus wijzigen |
| `/api/management/tenants` | GET / POST | Tenants ophalen / aanmaken |
| `/api/management/tenants/{id}/clients` | GET / POST | Clients van tenant beheren |
| `/api/management/commands/sync` | POST | Keycloak-synchronisatie forceren |
| `/api/management/admin/migrate-to-keycloak` | POST | Eenmalige migratie naar Keycloak |
| `/api/management/providers/roles` | GET | Beschikbare rollen ophalen |

### WQM Endpoints

| Endpoint | Methode | Vereiste Rol | Beschrijving |
|----------|---------|-------------|-------------|
| `/api/wqm/v1/authz/wqm/{userId}` | GET | `ROLE_WCS_WQM` | WQM autorisatiecode + rollen voor gebruiker |
| `/api/wqm/v1/report` | GET (CSV) | `ROLE_WCS_WQM_REPORT` | CSV-rapport alle actieve gebruikers + WQM-data |
| `/api/wqm/v1/tenant/tenant-type` | GET | `ROLE_WCS_WQM` | TenantType van huidige tenant |

---

## 8. Beveiligingsarchitectuur

### Rollen Overzicht

| Rolverdeling | Rollen | Doelgroep |
|--------------|--------|-----------|
| **Super Admin** | `ROLE_WCS_MANAGEMENT_SUPER_ADMIN` | Cipal Schaubroeck IT-beheer |
| **IT Admin** | `ROLE_WCS_MANAGEMENT_IT` | Cipal Schaubroeck IT-afdeling |
| **PHR Admin** | `ROLE_WCS_MANAGEMENT_PHR_ADMIN` | Payroll/HR functioneel beheer |
| **PHR Gebruiker** | `ROLE_WCS_MANAGEMENT_PHR_USER` | Payroll/HR consultants |
| **Klant Admin** | `ROLE_WCS_MANAGEMENT_CUSTOMER_ADMIN` | Gemeentelijk IT-beheer |
| **Klant Gebruiker** | `ROLE_WCS_MANAGEMENT_CUSTOMER_USER` | Gemeentelijke medewerkers |
| **LIMA API** | `ROLE_LIMA_API`, `ROLE_LIMA_CMD` | Externe HR-systemen |
| **WQM** | `ROLE_WCS_WQM`, `ROLE_WCS_WQMI`, `ROLE_WCS_WQM_REPORT` | WQM-module gebruikers |
| **CoreHR** | `ROLE_COREHR_ADMIN`, `ROLE_COREHR_EVALUATOR`, etc. | CoreHR integratie |

### Authenticatie & Autorisatie

- **Authenticatie**: Keycloak SSO (JWT Bearer tokens)
- **Autorisatie**: `@AuthorizeAction(Action.XXX)` annotaties op service-methoden — rolcontrole via AOP
- **Multi-tenant isolatie**: Elke API-aanroep is geïsoleerd tot de tenant van de ingelogde gebruiker
- **FAS-integratie**: Federale Authenticatiedienst voor verhoogde authenticatieniveaus

### Secrets Management

| Omgeving | Aanpak | Beoordeling |
|----------|--------|-------------|
| Productie | Docker Secrets (`/run/secrets/`) via `configtree:/run/secrets/` | ✅ Veilig |
| Integratie/Demo | Omgevingsvariabelen in properties | ⚠️ Controleren |
| Ontwikkeling | `wcs@pp` wachtwoord in `application-dev.properties` | ✅ Acceptabel (localhost only) |
| Test | H2 in-memory, geen externe secrets | ✅ Veilig |

---

## 9. Frontend Analyse

### Applicatiestructuur
```
src/app/
├── app.routes.ts          # 2 routes: /applicaties, /dossier-beheerder
├── app.component.ts       # Root component
├── shared/
│   ├── rest.service.ts    # Base HTTP service (alle API-calls)
│   ├── portal.store.ts    # State management (BehaviorSubject)
│   └── ...
├── applications/          # Module: applicatie-overzicht + bookmarks
└── contact/               # Module: dossierbeheerder contactinfo
```

### State Management Patroon
Het project gebruikt een **eenvoudig BehaviorSubject-patroon** (eigen `PortalStore`) in plaats van NgRx of Akita. Dit is passend gezien de beperkte scope van de frontend (slechts 2 modules).

```typescript
// PortalStore (vereenvoudigd)
export class PortalStore {
  private state$ = new BehaviorSubject<PortalState>(initialState);
  
  getApplications(): Observable<Application[]> { ... }
  setApplications(apps: Application[]): void { ... }
}
```

### Authenticatie Flow
```
Browser → Angular App
              │
              ▼ (keycloak-angular guard)
         Keycloak Server
              │ token
              ▼
         canActivateAuthRole (eigen Cipal lib)
              │ rol check
              ▼
         Applicatie geladen
```

### API Communicatie
Alle HTTP-aanroepen verlopen via `RestService` als base class:
- Base URL: `environment.portal_backend_url` → `/api` (prod) / `http://localhost:58082/api` (dev)
- Alle calls naar `/api/portal/...` endpoints

### Beoordeling Frontend
| Aspect | Beoordeling | Toelichting |
|--------|-------------|-------------|
| Moderniteit | ✅ Hoog | Angular 21, Tailwind 4, PrimeNG 21 |
| Complexiteit | ✅ Laag | Slechts 2 modules, beperkte scope |
| State management | ✅ Passend | BehaviorSubject voor kleine scope |
| Testbaarheid | ⚠️ Onduidelijk | Geen testbestanden zichtbaar in verkenning |
| Type-veiligheid | ✅ Goed | TypeScript strict, ESLint actief |
| Herbruikbaarheid | ✅ Goed | Eigen Cipal design system |

---

## 10. Kwaliteitsanalyse

### Testdekking

| Aspect | Bevinding | Beoordeling |
|--------|-----------|-------------|
| Unitteststrategie | 1-op-1 mirror: voor elke `*ServiceImpl.java` een `*ServiceImplTest.java` | ✅ Systematisch |
| Test framework | JUnit 5 + Mockito + AssertJ | ✅ Moderne stack |
| Externe services | WireMock voor alle externe API-stubs | ✅ Professioneel |
| Database tests | H2 in-memory voor integratietests | ✅ Geïsoleerd |
| Coverage meting | JaCoCo geconfigureerd (XML-rapport voor SonarQube) | ✅ CI-klaar |
| REST controller tests | Elke controller heeft corresponderende test | ✅ Volledig |
| WQM tests | `WqmReportServiceImplTest`, `WqmAuthzServiceImplTest` aanwezig | ✅ Goed |

### Technische Schuld

| Locatie | Beschrijving | Ernst |
|---------|-------------|-------|
| `User.java:114` | `"Really need to rewrite this, readability eeek."` in `isAllowedTo()` methode | Middel |
| `wcs-domain/` | TODO-dichtheid zeer laag (slechts 3 gevonden) — positief teken | Laag |
| Frontend | Geen duidelijke unit tests gevonden voor Angular-componenten | Middel |

### Code Stijl & Patronen

| Aspect | Bevinding | Beoordeling |
|--------|-----------|-------------|
| MapStruct strict mode | `unmappedTargetPolicy=ERROR` dwingt expliciete mapping af | ✅ Goed |
| Domein isolatie | `wcs-domain` heeft **geen** Spring-afhankelijkheden | ✅ Uitstekend |
| Builder patroon | Lombok `@Builder` gebruikt in entiteiten | ✅ Leesbaar |
| Lombok gebruik | `@Slf4j`, `@Getter`, `@Builder`, `@RequiredArgsConstructor` | ✅ Consistent |
| Null-veiligheid | SpotBugs annotations aanwezig | ✅ Proactief |
| AOP-autorisatie | `@AuthorizeAction` annotaties op service-methoden | ✅ Declaratief |
| Dependency Injection | Constructor injection (Lombok `@RequiredArgsConstructor`) | ✅ Testbaar |

### Documentatie

| Aspect | Beoordeling |
|--------|-------------|
| JavaDoc | Beperkt aanwezig (interne code, niet publieke API) |
| OpenAPI/Swagger | Aanwezig maar uitgeschakeld in prod |
| README | Aanwezig (niet gelezen in detail) |
| Architectuurdocumentatie | Niet gevonden in codebase |

---

## 11. Risico-inventaris

| ID | Risico | Waarschijnlijkheid | Impact | Mitigatie |
|----|--------|-------------------|--------|-----------|
| R-001 | **Keycloak 26.x versie-afhankelijkheid**: Breaking changes bij upgrade kunnen de `wcs-keycloak-service` breken | Middel | Hoog | Automatische integratietests voor Keycloak API-aanroepen |
| R-002 | **IBM Informix driver**: Verouderde of commercieel gelicentieerde driver (15.0.1.1) voor LIMA-integratie | Laag | Middel | Documenteer licentie en upgrade-pad |
| R-003 | **Frontend testdekking**: Geen zichtbare unit tests voor Angular-componenten | Hoog | Middel | E2E tests of component tests toevoegen |
| R-004 | **`isAllowedTo()` leesbaarheid** (User.java:114): Complexe autorisatielogica moeilijk te onderhouden | Middel | Middel | Refactoring naar Strategy-patroon |
| R-005 | **MapStruct strict mode**: Bij elke nieuwe entiteitsveld **moet** de mapper worden bijgewerkt — risico op compilatiefouten bij snelle iteratie | Hoog | Laag | CI/CD vangt dit op — acceptabel risico |
| R-006 | **Single-instance Keycloak**: Als Keycloak onbereikbaar is, kan WCS niet synchroniseren | Laag | Hoog | Circuit breaker + retry-logica + monitoring |
| R-007 | **Liquibase Java-based changesets**: Moeilijker te reviewen dan XML/SQL changesets; risico op niet-idempotente migraties | Middel | Hoog | Code reviews afdwingen voor DB-changesets |
| R-008 | **LIMA Informix-koppeling**: Externe afhankelijkheid op legacy IBM-databron voor HR-synchronisatie | Laag | Hoog | Fallback-strategie documenteren |
| R-009 | **Angular 21**: Zeer recente versie — eigen Cipal libs (`phr-ng-keycloak`, `jangosquare-*`) moeten compatibel blijven | Middel | Middel | Versie-lockstrategie voor eigen libs |
| R-010 | **Productie-secrets via Docker secrets**: Goed patroon, maar vereist correcte Docker Swarm/Compose setup | Laag | Hoog | Operationele runbook voor secret rotatie |

---

## 12. Aanbevelingen

### Matrix (Prioriteit × Impact × Inspanning)

| ID | Aanbeveling | Impact | Inspanning | Prioriteit |
|----|-------------|--------|------------|------------|
| A-001 | **Refactor `User.isAllowedTo()`** — extractie naar dedicated `UserAuthorizationService` met leesbare rule-objecten (Strategy-patroon) | Middel | Klein | **P1** |
| A-002 | **Frontend unit tests toevoegen** voor Angular-componenten (Jest + Angular Testing Library) — minimaal kritieke UI-flows | Hoog | Middel | **P1** |
| A-003 | **Architectuurdocumentatie** aanmaken (ADR's voor technologiekeuzes: waarom Keycloak, waarom MariaDB + Informix, waarom geen NgRx) | Middel | Klein | **P1** |
| A-004 | **Keycloak integratiemonitor** implementeren: health check die Keycloak-sync-status bewaakt en alerting triggert bij langdurige DIRTY-status | Hoog | Middel | **P2** |
| A-005 | **Liquibase changeset review-proces** formaliseren: geen Java-changeset mag naar main zonder peer review van een DBA/architect | Hoog | Klein | **P2** |
| A-006 | **Circuit breaker** voor externe integraties (Keycloak, LIMA, Payflip) via Spring Resilience4J | Middel | Middel | **P2** |
| A-007 | **OpenAPI-documentatie in CI** genereren en hosten (intern, niet publiek) — waardevol voor nieuwe ontwikkelaars | Middel | Klein | **P2** |
| A-008 | **Frontend E2E-tests** (Cypress of Playwright) voor de kritieke portaalflows (inloggen, applicaties bekijken, dossierbeheerder) | Middel | Groot | **P3** |
| A-009 | **Upgrade Informix-driver** evalueren of LIMA-integratie migreren naar moderne REST-API indien mogelijk | Middel | Groot | **P3** |
| A-010 | **Angular lazy loading optimaliseren**: de 2 modules zijn reeds slim gestructureerd; lazy loading toevoegen voor betere initiaallaadtijd | Laag | Klein | **P3** |

---

## 13. Conclusie

WCS is een **goed gestructureerde, enterprise-kwaliteit IAM-beheeroplossing** die bouwt op solide principes:

### Sterke punten ✅
1. **Duidelijke lagenarchitectuur** met expliciete domein-isolatie (`wcs-domain` zonder Spring)
2. **Systematische testdekking** met 1-op-1 service/test-klasse correspondentie + WireMock
3. **Veilig secrets management** via Docker secrets in productie
4. **Declaratieve autorisatie** via `@AuthorizeAction` annotaties (AOP)
5. **Moderne tech stack** (Java 17, Spring Boot 3.5.x, Angular 21)
6. **Strikte MapStruct-configuratie** voorkomt unmapped fields in productie
7. **Multi-module Maven** met duidelijke verantwoordelijkheidsgrenzen

### Aandachtspunten ⚠️
1. **Frontend testdekking** ontbreekt merkbaar
2. **`isAllowedTo()` methode** vraagt om refactoring (eigen technische schuld comment)
3. **Architectuurdocumentatie** ontbreekt (geen ADR's gevonden)
4. **IBM Informix-afhankelijkheid** introduceert legacy risico voor LIMA-integratie

### Geschiktheid voor modernisering
Het systeem is **goed gepositioneerd voor verdere modernisering**:
- De domein-isolatie maakt het mogelijk services te extraheren naar microservices
- De Keycloak-integratie is reeds geabstraheerd achter een dedicated service
- De Angular-frontend is relatief klein en eenvoudig te vervangen/uitbreiden

**Aanbevolen volgorde van vervolgstappen:**
1. Architectuurdocumentatie (A-003) — laagste inspanning, hoogste kenniswaarde
2. `isAllowedTo()` refactoring (A-001) — kleine ingreep, grote onderhoudswinst
3. Frontend tests (A-002) — voorwaarde voor veilige toekomstige uitbreidingen
4. Monitoring & circuit breakers (A-004, A-006) — productie-robuustheid

---

## 14. Glossarium

| Term | Definitie |
|------|-----------|
| **WCS** | Web Client Service — het IAM-beheerplatform van Cipal Schaubroeck |
| **Tenant** | Een organisatie (gemeente, OCMW) die WCS gebruikt voor gebruikersbeheer |
| **TenantType** | Het type organisatie: CSPAYROLLHR, FSSC, SC, PROXY |
| **Client** | Een OIDC-applicatie die is geregistreerd in Keycloak via WCS |
| **LIMA** | Externe HR/payroll-integratieservice waarmee WCS gebruikers synchroniseert |
| **WQM** | Werknemers Query Module — specifieke autorisatiemodule met auth-codes voor werknemers |
| **SyncStatus** | Status van de synchronisatie van een entiteit naar Keycloak: PREPARING → READY → BUSY → OK/DIRTY |
| **UserStatus** | Status van een gebruiker: NEW → READY → OK, DISABLED, REMOVED |
| **FAS** | Federale Authenticatiedienst — Belgische overheidsauthenticatiedienst voor verhoogde assurance levels |
| **Payflip** | Externe SaaS voor fietsleasingbeheer, gekoppeld via OAuth2/Auth0 |
| **CoreHR** | Payroll/HR-systeem gekoppeld via LIMA-integratie |
| **PHR** | PersoneelsHRbeheer — Cipal Schaubroeck product voor HR-beheer |
| **MapStruct** | Java bean mapping framework, compileert naar directe getter/setter aanroepen |
| **Liquibase** | Database schema migration tool, WCS gebruikt Java-based changesets |
| **Docker Secrets** | Docker mechanisme voor veilige secrets injectie via `/run/secrets/` |
| **@AuthorizeAction** | Custom AOP annotatie die rolcontrole afdwingt op service-methoden |
| **jangosquare** | Eigen UI component library van Cipal Schaubroeck |
| **phr-ng-keycloak** | Eigen Angular Keycloak integratie library van Cipal Schaubroeck |

---

*Rapport gegenereerd door VorstersNV Consultancy — Alle bevindingen zijn gebaseerd op statische codeanalyse zonder uitvoering van de applicatie. Bestandsreferenties verwijzen naar de `wcs-backend-develop` en `wcs-portal-develop` branches op het moment van analyse.*
