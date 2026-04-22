# Lokale Setup Gids: WCS + LIMA + PHR GlobalConfig

> **Doelgroep**: Ontwikkelaars die alle vijf componenten lokaal willen draaien voor integratieontwikkeling  
> **Laatste update**: Juni 2025  
> **Java versie**: 17 (verplicht voor alle projecten)

---

## Inhoudsopgave

1. [Overzicht & Communicatiematrix](#1-overzicht--communicatiematrix)
2. [Vereisten](#2-vereisten)
3. [Architectuurdiagram](#3-architectuurdiagram)
4. [Dependency-volgorde & Opstartgids](#4-dependency-volgorde--opstartgids)
   - [Stap 1: Docker Infrastructure](#stap-1-docker-infrastructure-mariadb--keycloak)
   - [Stap 2: phr-globalconfig-core](#stap-2-phr-globalconfig-core-standalone)
   - [Stap 3: WCS Backend](#stap-3-wcs-backend)
   - [Stap 4: phr-globalconfig](#stap-4-phr-globalconfig-frontend--backend)
   - [Stap 5: WCS Portal](#stap-5-wcs-portal-frontend)
5. [MariaDB Setup](#5-mariadb-setup)
6. [Keycloak Setup](#6-keycloak-setup)
7. [Lokale Config Overschrijvingen](#7-lokale-config-overschrijvingen)
8. [Veelvoorkomende Problemen & Oplossingen](#8-veelvoorkomende-problemen--oplossingen)
9. [Verificatie](#9-verificatie)
10. [Docker Compose Voorbeeld](#10-docker-compose-voorbeeld)

---

## 1. Overzicht & Communicatiematrix

### De vijf componenten

| # | Project | Type | Poort | Database | Beschrijving |
|---|---------|------|-------|----------|--------------|
| 1 | **wcs-backend** | Spring Boot API | `58082` | MariaDB `53306` | Identity & Access Management (multi-tenant) |
| 2 | **wcs-portal** | Angular SPA | `4200` | — | Frontend voor WCS beheer |
| 3 | **phr-globalconfig** | Spring Boot + Angular | `54210` (FE) | Via Core | Full-stack HR configuratiebeheer |
| 4 | **phr-globalconfig-core** | Spring Boot microservice | `80` | H2 (dev) / MariaDB (integratie) | Rekenlogica: loonschalen, mappings, bonussen |
| 5 | **lpbunified** | LPB rekenmotor | Variabel | — | LIMA loonberekeningsprogramma (intern) |

### Communicatiematrix

```
Component             → Roept aan              Via
─────────────────────────────────────────────────────────────────
phr-globalconfig      → phr-globalconfig-core  Spring Cloud OpenFeign (GlobalconfigCoreClient)
phr-globalconfig      → wcs-backend            Spring Cloud OpenFeign (WcsClient)
wcs-backend           → Keycloak               OAuth2 JWT validatie
wcs-backend           → LIMA (lpbunified)      wcs-lima-service module
wcs-portal            → wcs-backend            REST API calls
Alle services         → Keycloak               JWT token validatie (realm: cspayrollhr)
```

### Kritische dependency-volgorde

```
Keycloak → MariaDB → phr-globalconfig-core → wcs-backend → phr-globalconfig → wcs-portal
```

> ⚠️ **Belangrijk**: `phr-globalconfig` zal crashen bij opstarten als `phr-globalconfig-core` of `wcs-backend` niet bereikbaar zijn (Feign clients proberen verbinding bij startup).

---

## 2. Vereisten

### Verplichte software

| Software | Minimale versie | Aanbevolen versie | Verificatie |
|----------|----------------|-------------------|-------------|
| **Java (JDK)** | 17 | 17.0.x (LTS) | `java -version` |
| **Maven** | 3.8.x | 3.9.x | `mvn -version` |
| **Gradle** | 7.x (via wrapper) | Via `./gradlew` | `./gradlew --version` |
| **Node.js** | 18.x | 20.x LTS | `node -version` |
| **npm** | 9.x | 10.x | `npm -version` |
| **Docker Desktop** | 24.x | Latest | `docker --version` |
| **Docker Compose** | 2.x | Latest | `docker compose version` |
| **Git** | 2.x | Latest | `git --version` |

### Aanbevolen tools

```bash
# IntelliJ IDEA (Ultimate aanbevolen voor Spring Boot + Angular)
# VS Code met Angular Language Service extension
# DBeaver of TablePlus voor MariaDB inzage
# Keycloak Admin Console (web UI op http://localhost:8080)
```

### Java versie controle en instelling

```powershell
# Controleer huidige versie
java -version

# Als JAVA_HOME niet correct staat (Windows PowerShell):
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.x-hotspot"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"

# Permanent instellen via System Properties > Environment Variables
```

> ⚠️ **Gebruik GEEN Java 21** — alle projecten zijn gebouwd met Java 17. Hogere versies kunnen compilatiefouten veroorzaken door module-systeem wijzigingen.

---

## 3. Architectuurdiagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        LOKALE ONTWIKKELOMGEVING                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐ │
│  │   Browser    │────▶│           DOCKER INFRASTRUCTURE                  │ │
│  │  (localhost) │     │  ┌─────────────────┐  ┌─────────────────────┐   │ │
│  └──────┬───────┘     │  │   Keycloak      │  │     MariaDB         │   │ │
│         │             │  │   :8080         │  │     :53306          │   │ │
│         │             │  │   realm:        │  │   DB: wcs_local     │   │ │
│         │             │  │   cspayrollhr   │  │   DB: globalconfig  │   │ │
│         │             │  └────────┬────────┘  └──────────┬──────────┘   │ │
│         │             └───────────┼──────────────────────┼──────────────┘ │
│         │                         │ JWT validatie         │ JDBC           │
│         │                         │                       │                │
│  ┌──────▼───────┐         ┌───────▼───────────────────────▼──────────┐    │
│  │  WCS Portal  │         │              WCS Backend                  │    │
│  │  Angular SPA │────────▶│         wcs-backend-develop               │    │
│  │  :4200       │  REST   │              :58082                       │    │
│  └──────────────┘         │   Modules: wcs-lima-service               │    │
│                           │            wcs-keycloak-service           │    │
│                           │            wcs-management-service         │    │
│                           └──────────────────┬────────────────────────┘    │
│                                              │ WcsClient (Feign)           │
│  ┌────────────────────────────────┐          │                             │
│  │       phr-globalconfig         │          │                             │
│  │  Frontend :54210 (Angular)     │          │                             │
│  │  Backend  :8090 (Spring Boot)  │──────────┘                            │
│  │  client: wdc-globalconfig      │                                        │
│  └────────────────┬───────────────┘                                        │
│                   │ GlobalconfigCoreClient (Feign)                         │
│                   ▼                                                         │
│  ┌────────────────────────────────┐                                        │
│  │     phr-globalconfig-core      │                                        │
│  │         :80                    │                                        │
│  │   /phr-globalconfig-core-      │                                        │
│  │         backend                │                                        │
│  │   H2 (dev) | MariaDB (intgr)  │                                        │
│  └────────────────────────────────┘                                        │
│                                                                             │
│  ┌────────────────────────────────┐                                        │
│  │         lpbunified             │                                        │
│  │    (LIMA rekenmotor)           │                                        │
│  │    Standalone / via WCS        │                                        │
│  └────────────────────────────────┘                                        │
│                                                                             │
│  NEXUS npm registry: https://repo.int.cipal.be/nexus3/repository/npm/      │
│  (Vereist VPN of intern netwerk voor Angular packages!)                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Dependency-volgorde & Opstartgids

---

### Stap 1: Docker Infrastructure (MariaDB + Keycloak)

#### 1.1 Maak de Docker Compose aan

Maak het bestand `docker-compose.local.yml` aan in een werkmap (bijv. `C:\Users\kvo\Desktop\local-dev\`). Zie [Sectie 10](#10-docker-compose-voorbeeld) voor de volledige inhoud.

#### 1.2 Start de containers

```powershell
cd C:\Users\kvo\Desktop\local-dev

# Start alle infrastructure containers
docker compose -f docker-compose.local.yml up -d

# Controleer of alles draait
docker compose -f docker-compose.local.yml ps

# Bekijk logs
docker compose -f docker-compose.local.yml logs -f mariadb
docker compose -f docker-compose.local.yml logs -f keycloak
```

#### 1.3 Wacht op Keycloak

Keycloak heeft ±30-60 seconden nodig om op te starten. Controleer:

```powershell
# Wacht tot Keycloak bereikbaar is
Start-Sleep -Seconds 60

# Test health
Invoke-WebRequest -Uri "http://localhost:8080/health/ready" -UseBasicParsing
# Verwacht: {"status":"UP"} of HTTP 200
```

#### 1.4 Initialiseer Keycloak realm

Zie [Sectie 6: Keycloak Setup](#6-keycloak-setup) voor de gedetailleerde realm configuratie.

---

### Stap 2: phr-globalconfig-core (Standalone)

> **Waarom eerst?** `phr-globalconfig` heeft een Feign client naar deze service. Als core niet draait, faalt phr-globalconfig bij startup.

#### 2.1 Navigeer naar het project

```powershell
cd C:\Users\kvo\Desktop\phr-globalconfig-core-develop
```

#### 2.2 Controleer de tenant config

```powershell
# Verifieer dat de tenant config bestaat
Get-Content "backend\config\tenant-cspayrollhr.properties"
```

Het bestand moet minimaal bevatten:

```properties
# backend/config/tenant-cspayrollhr.properties
realm.uuid=cspayrollhr
spring.datasource.url=jdbc:h2:mem:globalconfig-core;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE
spring.datasource.driver-class-name=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=
spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
```

#### 2.3 Build het project

```powershell
# Gradle wrapper gebruiken (NIET globale gradle!)
.\gradlew build -x test

# Verwacht: BUILD SUCCESSFUL
```

#### 2.4 Start met H2 profiel (aanbevolen voor lokale dev)

```powershell
# Kritische environment variable voor tenant config locatie
$env:MULTITENANT_CONFIG_LOCATION = "backend\config"

# Start met dev + h2 profielen
.\gradlew bootRun --args="--spring.profiles.active=dev,h2"

# Of via jar:
.\gradlew bootJar
java -jar backend\build\libs\*.jar `
  --spring.profiles.active=dev,h2 `
  --multitenant.config.location=backend\config
```

#### 2.5 Verificatie

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:80/phr-globalconfig-core-backend/actuator/health" -UseBasicParsing

# Swagger UI (als aanwezig)
Start-Process "http://localhost:80/phr-globalconfig-core-backend/swagger-ui.html"
```

---

### Stap 3: WCS Backend

#### 3.1 Navigeer naar het project

```powershell
cd C:\Users\kvo\Desktop\wcs-backend-develop
```

#### 3.2 Kopieer de lokale configuratie

```powershell
# ÉÉNMALIG: kopieer het sample naar local/
if (-not (Test-Path "local")) {
    Copy-Item -Recurse "local.sample" "local"
    Write-Host "local/ map aangemaakt. Pas de configuratie aan!"
} else {
    Write-Host "local/ map bestaat al."
}
```

#### 3.3 Pas de lokale configuratie aan

Bewerk `local/application-local.properties` (of het equivalente bestand in `local/`):

```properties
# local/application-local.properties

# MariaDB connectie (poort 53306 - NIET de standaard 3306!)
spring.datasource.url=jdbc:mariadb://localhost:53306/wcs_local?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC
spring.datasource.username=wcs_user
spring.datasource.password=wcs_password

# Keycloak JWT validatie
spring.security.oauth2.resourceserver.jwt.issuer-uri=http://localhost:8080/realms/cspayrollhr
spring.security.oauth2.resourceserver.jwt.jwk-set-uri=http://localhost:8080/realms/cspayrollhr/protocol/openid-connect/certs

# Keycloak admin (voor wcs-keycloak-service)
keycloak.server-url=http://localhost:8080
keycloak.realm=cspayrollhr
keycloak.client-id=wcs-backend
keycloak.client-secret=VERVANG_MET_ECHTE_SECRET

# LIMA integratie (pas aan indien lpbunified lokaal draait)
lima.service.url=http://localhost:LIMA_PORT

# Server poort
server.port=58082

# Liquibase
spring.liquibase.enabled=true
spring.liquibase.change-log=classpath:db/changelog/db.changelog-master.xml
```

#### 3.4 Build het project

```powershell
# Maven multi-module build (sla tests over voor snelheid)
mvn clean install -DskipTests

# Verwacht: [INFO] BUILD SUCCESS voor alle modules
# Let op de volgorde: domain → db → persistence → service → rest → backend
```

#### 3.5 Start de applicatie

```powershell
cd wcs-backend
java -jar target/wcs-backend-*.jar --spring.profiles.active=default,local

# Of via Maven:
mvn spring-boot:run -pl wcs-backend -Dspring-boot.run.profiles=default,local
```

#### 3.6 Verificatie

```powershell
Invoke-WebRequest -Uri "http://localhost:58082/actuator/health" -UseBasicParsing
# Verwacht: {"status":"UP"}
```

---

### Stap 4: phr-globalconfig (Frontend + Backend)

> **Vereiste**: phr-globalconfig-core (:80) én wcs-backend (:58082) moeten draaien.

#### 4.1 Navigeer naar het project

```powershell
cd C:\Users\kvo\Desktop\phr-globalconfig-develop
```

#### 4.2 Configureer de tenant properties

```powershell
Get-Content "config\tenant-cspayrollhr.properties"
```

Pas aan zodat de Feign clients de juiste URLs gebruiken:

```properties
# config/tenant-cspayrollhr.properties
realm.uuid=cspayrollhr

# Feign client URL's
globalconfig.core.url=http://localhost:80/phr-globalconfig-core-backend
wcs.client.url=http://localhost:58082

# Datasource (roept door naar core, geen eigen DB in eenvoudige modus)
spring.datasource.url=jdbc:mariadb://localhost:53306/globalconfig?useSSL=false
spring.datasource.username=globalconfig_user
spring.datasource.password=globalconfig_password

# Keycloak
spring.security.oauth2.resourceserver.jwt.issuer-uri=http://localhost:8080/realms/cspayrollhr
```

#### 4.3 Start de backend

```powershell
.\gradlew bootRun
# Backend start op configureerbare poort (check application.properties voor exacte poort)
```

#### 4.4 Installeer frontend dependencies

> ⚠️ **NPM Registry is intern (Nexus)!** Zie [Sectie 8](#8-veelvoorkomende-problemen--oplossingen) als je buiten het Cipal netwerk werkt.

```powershell
cd frontend

# Controleer of .npmrc correct is ingesteld
Get-Content .npmrc
# Moet bevatten: registry=https://repo.int.cipal.be/nexus3/repository/npm/

# Installeer dependencies
npm install

# Als dit faalt door registry, zie Sectie 8 voor workarounds
```

#### 4.5 Start de frontend dev server

```powershell
# Vanuit frontend/ map
npm start
# Start op poort 54210 met HMR en proxy naar backend
```

---

### Stap 5: WCS Portal (Frontend)

```powershell
cd C:\Users\kvo\Desktop\wcs-portal-develop\frontend

# Gradle wrapper (als Gradle gebruikt wordt voor deps)
cd ..
.\gradlew npmInstall  # of equivalente taak

# Frontend dev server
cd frontend
npm start
# Standaard Angular dev server, typisch :4200
```

---

## 5. MariaDB Setup

### 5.1 Databases en gebruikers aanmaken

Verbind met MariaDB via Docker (na stap 1):

```powershell
# Verbind via Docker exec
docker exec -it local-mariadb mariadb -u root -prootpassword

# Of via externe tool (DBeaver/TablePlus):
# Host: localhost, Port: 53306, User: root, Password: rootpassword
```

```sql
-- WCS database
CREATE DATABASE IF NOT EXISTS wcs_local
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'wcs_user'@'%' IDENTIFIED BY 'wcs_password';
GRANT ALL PRIVILEGES ON wcs_local.* TO 'wcs_user'@'%';

-- GlobalConfig database (indien MariaDB gebruikt i.p.v. H2)
CREATE DATABASE IF NOT EXISTS globalconfig
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'globalconfig_user'@'%' IDENTIFIED BY 'globalconfig_password';
GRANT ALL PRIVILEGES ON globalconfig.* TO 'globalconfig_user'@'%';

-- GlobalConfig Core database (voor integratie modus)
CREATE DATABASE IF NOT EXISTS globalconfig_core
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'gccore_user'@'%' IDENTIFIED BY 'gccore_password';
GRANT ALL PRIVILEGES ON globalconfig_core.* TO 'gccore_user'@'%';

FLUSH PRIVILEGES;
SHOW DATABASES;
```

### 5.2 Liquibase (automatisch bij opstarten)

Liquibase draait automatisch bij de eerste start van WCS Backend. De changelogs staan in:
- `wcs-db/src/main/resources/db/changelog/`

**Als Liquibase faalt:**

```powershell
# Reset de Liquibase lock (als een eerdere run vastliep)
docker exec -it local-mariadb mariadb -u wcs_user -pwcs_password wcs_local \
  -e "DELETE FROM DATABASECHANGELOGLOCK; UPDATE DATABASECHANGELOGLOCK SET LOCKED=0, LOCKGRANTED=NULL, LOCKEDBY=NULL WHERE ID=1;"
```

### 5.3 MariaDB configuratie voor performance

Voeg toe aan de MariaDB Docker configuratie (via `my.cnf`):

```ini
[mysqld]
# Performance voor lokale dev
innodb_buffer_pool_size = 256M
max_connections = 100
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Tijdzone
default-time-zone = '+01:00'
```

---

## 6. Keycloak Setup

### 6.1 Toegang tot Keycloak Admin Console

Na het starten van Docker:

```
URL:      http://localhost:8080
Username: admin
Password: admin  (of wat je instelde in docker-compose)
```

### 6.2 Realm `cspayrollhr` aanmaken

**Via de Admin Console:**

1. Klik op het realm-dropdown linksboven → **Create Realm**
2. Realm name: `cspayrollhr`
3. Enabled: **ON**
4. Klik **Create**

**Of via Keycloak CLI (kcadm):**

```powershell
docker exec -it local-keycloak /opt/keycloak/bin/kcadm.sh config credentials `
  --server http://localhost:8080 `
  --realm master `
  --user admin `
  --password admin

docker exec -it local-keycloak /opt/keycloak/bin/kcadm.sh create realms `
  -s realm=cspayrollhr `
  -s enabled=true
```

### 6.3 Clients configureren

#### Client: `wcs-backend`

```json
{
  "clientId": "wcs-backend",
  "name": "WCS Backend Service",
  "enabled": true,
  "clientAuthenticatorType": "client-secret",
  "secret": "GENEREER_EEN_VEILIGE_SECRET",
  "serviceAccountsEnabled": true,
  "directAccessGrantsEnabled": true,
  "protocol": "openid-connect",
  "publicClient": false
}
```

Via Admin Console:
1. Ga naar realm `cspayrollhr` → **Clients** → **Create client**
2. Client ID: `wcs-backend`
3. Client type: `OpenID Connect`
4. **Authentication**: ON
5. Ga naar **Credentials** tab → kopieer de Client Secret naar je `local/application-local.properties`

#### Client: `wdc-globalconfig`

```json
{
  "clientId": "wdc-globalconfig",
  "name": "PHR GlobalConfig Client",
  "enabled": true,
  "publicClient": true,
  "redirectUris": ["http://localhost:54210/*"],
  "webOrigins": ["http://localhost:54210"],
  "protocol": "openid-connect",
  "standardFlowEnabled": true
}
```

#### Client: `wcs-portal` (voor de Angular SPA)

```json
{
  "clientId": "wcs-portal",
  "enabled": true,
  "publicClient": true,
  "redirectUris": ["http://localhost:4200/*"],
  "webOrigins": ["http://localhost:4200"],
  "protocol": "openid-connect",
  "standardFlowEnabled": true
}
```

### 6.4 Test gebruikers aanmaken

```
Realm: cspayrollhr → Users → Create user

Gebruiker 1 (admin):
  Username: admin-local
  Email:    admin@local.dev
  Roles:    admin (of WCS-specifieke rollen)

Gebruiker 2 (standaard gebruiker):
  Username: user-local
  Email:    user@local.dev
  Roles:    user
```

Stel wachtwoorden in: **Users** → selecteer gebruiker → **Credentials** → **Set password** (Temporary: OFF).

### 6.5 Tenant UUID koppeling

De tenant UUID `cspayrollhr` moet overeenkomen in alle services. Controleer:

```properties
# In phr-globalconfig/config/tenant-cspayrollhr.properties
realm.uuid=cspayrollhr

# In phr-globalconfig-core/backend/config/tenant-cspayrollhr.properties
realm.uuid=cspayrollhr
```

De bestandsnaam (`tenant-cspayrollhr.properties`) bepaalt de tenant identificatie — dit moet overeenkomen met de Keycloak realm naam.

---

## 7. Lokale Config Overschrijvingen

### 7.1 WCS Backend — `local/` configuratie

```powershell
# Structuur na kopiëren van local.sample/
wcs-backend-develop/
├── local.sample/          # Template (commit in Git)
│   └── application-local.properties.sample
└── local/                 # Jouw lokale config (in .gitignore!)
    └── application-local.properties
```

**Minimale `local/application-local.properties`:**

```properties
# === DATABASE ===
spring.datasource.url=jdbc:mariadb://localhost:53306/wcs_local?useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true
spring.datasource.username=wcs_user
spring.datasource.password=wcs_password
spring.datasource.driver-class-name=org.mariadb.jdbc.Driver
spring.jpa.database-platform=org.hibernate.dialect.MariaDBDialect

# === KEYCLOAK ===
spring.security.oauth2.resourceserver.jwt.issuer-uri=http://localhost:8080/realms/cspayrollhr
spring.security.oauth2.resourceserver.jwt.jwk-set-uri=http://localhost:8080/realms/cspayrollhr/protocol/openid-connect/certs
keycloak.server-url=http://localhost:8080
keycloak.realm=cspayrollhr
keycloak.client-id=wcs-backend
keycloak.client-secret=JOUW_CLIENT_SECRET_HIER

# === SERVER ===
server.port=58082
server.servlet.context-path=/

# === LOGGING ===
logging.level.root=INFO
logging.level.be.cipal=DEBUG

# === LIQUIBASE ===
spring.liquibase.enabled=true

# === CORS (voor lokale Angular dev) ===
cors.allowed-origins=http://localhost:4200,http://localhost:54210
```

### 7.2 phr-globalconfig-core — Tenant Config

```powershell
# Locatie: backend/config/tenant-cspayrollhr.properties
# Env var: MULTITENANT_CONFIG_LOCATION=backend\config
```

**H2 modus (aanbevolen voor snel opstarten):**

```properties
realm.uuid=cspayrollhr
spring.datasource.url=jdbc:h2:mem:gccore_cspayrollhr;DB_CLOSE_DELAY=-1;MODE=MySQL
spring.datasource.driver-class-name=org.h2.Driver
spring.datasource.username=sa
spring.datasource.password=
spring.jpa.database-platform=org.hibernate.dialect.H2Dialect
spring.h2.console.enabled=true
spring.h2.console.path=/h2-console
spring.liquibase.enabled=true
```

**MariaDB modus (voor integratie testing):**

```properties
realm.uuid=cspayrollhr
spring.datasource.url=jdbc:mariadb://localhost:53306/globalconfig_core?useSSL=false&serverTimezone=UTC
spring.datasource.driver-class-name=org.mariadb.jdbc.Driver
spring.datasource.username=gccore_user
spring.datasource.password=gccore_password
spring.jpa.database-platform=org.hibernate.dialect.MariaDBDialect
spring.liquibase.enabled=true
```

### 7.3 phr-globalconfig — Tenant + Feign Config

```properties
# config/tenant-cspayrollhr.properties
realm.uuid=cspayrollhr

# Feign client base URLs
globalconfig-core.url=http://localhost:80
wcs.url=http://localhost:58082

# Keycloak
spring.security.oauth2.resourceserver.jwt.issuer-uri=http://localhost:8080/realms/cspayrollhr

# Frontend proxy target (voor Angular dev server)
# Zie frontend/proxy.conf.json
```

**Frontend proxy configuratie** (`frontend/proxy.conf.json`):

```json
{
  "/phr-globalconfig-backend": {
    "target": "http://localhost:BACKEND_POORT",
    "secure": false,
    "logLevel": "debug",
    "changeOrigin": true
  }
}
```

### 7.4 Angular `.npmrc` configuratie

Beide Angular projecten (`wcs-portal` en `phr-globalconfig`) gebruiken de interne Nexus npm registry.

**Controleer `.npmrc` in de frontend/ map:**

```ini
registry=https://repo.int.cipal.be/nexus3/repository/npm/
always-auth=true
; _auth=BASE64_VAN_GEBRUIKER:WACHTWOORD  (als authenticatie vereist is)
```

---

## 8. Veelvoorkomende Problemen & Oplossingen

---

### ❌ Probleem 1: npm install faalt — Nexus registry niet bereikbaar

**Foutmelding:**
```
npm ERR! code ENOTFOUND
npm ERR! errno ENOTFOUND
npm ERR! network request to https://repo.int.cipal.be/nexus3/... failed
```

**Oorzaak:** Je bent niet verbonden met het interne Cipal netwerk.

**Oplossingen:**

```powershell
# Oplossing A: Verbind met VPN (aanbevolen)
# Start Cipal VPN client en probeer opnieuw

# Oplossing B: Gebruik de publieke npm registry als tijdelijke workaround
# (Werkt NIET voor interne @cipalschaubroeck/* packages!)
npm install --registry https://registry.npmjs.org

# Oplossing C: Wijzig tijdelijk .npmrc
# Vervang registry naar https://registry.npmjs.org
# LET OP: @cipalschaubroeck packages zijn NIET beschikbaar op public npm

# Oplossing D: Gebruik een gecachte node_modules map
# Als een collega node_modules heeft, kopieer en gebruik dat
```

> ⚠️ **@cipalschaubroeck/phr-ng-keycloak** is een intern package. Zonder Nexus toegang kun je de Angular app niet bouwen. **VPN is vereist.**

---

### ❌ Probleem 2: Keycloak JWT validatie faalt — "Invalid token issuer"

**Foutmelding:**
```
401 Unauthorized
{"error": "invalid_token", "error_description": "Token issuer mismatch"}
```

**Oorzaak:** De `issuer-uri` in je applicatie-configuratie komt niet overeen met de `iss` claim in het JWT token.

**Oplossingen:**

```bash
# Stap 1: Decode het JWT token en check de issuer
# Ga naar https://jwt.io en plak je token
# Verwachte iss: http://localhost:8080/realms/cspayrollhr

# Stap 2: Controleer je configuratie
spring.security.oauth2.resourceserver.jwt.issuer-uri=http://localhost:8080/realms/cspayrollhr
# NIET: https (als Keycloak lokaal draait zonder SSL)
# NIET: 127.0.0.1 als het token localhost zegt

# Stap 3: Als Keycloak achter een proxy zit, stel frontendUrl in:
# Keycloak Admin → Realm Settings → Frontend URL = http://localhost:8080
```

---

### ❌ Probleem 3: WCS Backend start niet — Liquibase checksum mismatch

**Foutmelding:**
```
liquibase.exception.ValidationFailedException: 
Validation Failed: 1 change sets check sum
```

**Oplossingen:**

```sql
-- Verbind met MariaDB en fix de checksum
UPDATE wcs_local.DATABASECHANGELOG 
SET MD5SUM = NULL 
WHERE ID = 'PROBLEMATISCHE_CHANGESET_ID';

-- Of: complete reset (VERLIES ALLE DATA!)
DROP DATABASE wcs_local;
CREATE DATABASE wcs_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- Herstart WCS Backend → Liquibase herloopt alles
```

---

### ❌ Probleem 4: Port conflict op poort 53306 of 8080

**Foutmelding:**
```
Error response from daemon: driver failed programming external connectivity: 
Bind for 0.0.0.0:53306 failed: port is already allocated
```

**Oplossingen:**

```powershell
# Zoek welk process de poort gebruikt (Windows)
netstat -ano | findstr :53306
netstat -ano | findstr :8080

# Stop het process (vervang PID met gevonden PID)
Stop-Process -Id PID -Force

# Of: wijzig de poort in docker-compose.local.yml
# services.mariadb.ports: "53307:3306"  (en pas ook application properties aan)
```

---

### ❌ Probleem 5: phr-globalconfig faalt bij startup — Feign connect refused

**Foutmelding:**
```
feign.RetryableException: Connection refused executing GET http://localhost:80/...
```

**Oorzaak:** `phr-globalconfig-core` draait niet of is nog niet klaar.

**Oplossing:**

```powershell
# Stap 1: Controleer of globalconfig-core draait
Invoke-WebRequest -Uri "http://localhost:80/phr-globalconfig-core-backend/actuator/health" -UseBasicParsing

# Stap 2: Als het niet draait, start het eerst (zie Stap 2)
# Stap 3: Wacht tot health = UP
# Stap 4: Herstart phr-globalconfig
```

**Tijdelijke workaround** — Disable Feign bij startup (voor frontend-only ontwikkeling):

```yaml
# application-local.yaml
spring:
  cloud:
    openfeign:
      lazy-attributes-resolution: true  # Vertraagt Feign initialisatie
```

---

### ❌ Probleem 6: MariaDB poort 53306 — drivers en connectiestrings

**Veelgemaakte fout:** Standaard JDBC strings gebruiken poort 3306.

```properties
# FOUT:
spring.datasource.url=jdbc:mariadb://localhost:3306/wcs_local

# CORRECT (poort 53306!):
spring.datasource.url=jdbc:mariadb://localhost:53306/wcs_local?useSSL=false&serverTimezone=UTC&allowPublicKeyRetrieval=true
```

---

### ❌ Probleem 7: Java versie conflict

**Foutmelding:**
```
UnsupportedClassVersionError: ... has been compiled by a more recent version of Java
```

**Oplossing:**

```powershell
# Controleer welke Java wordt gebruikt
java -version
$env:JAVA_HOME

# Als IntelliJ IDEA wordt gebruikt:
# File → Project Structure → Project SDK → Java 17
# File → Project Structure → Modules → elk module → Java 17

# Maven: controleer maven-compiler-plugin in pom.xml
# Moet zijn: <source>17</source> <target>17</target>
```

---

### ❌ Probleem 8: H2 Console niet bereikbaar voor globalconfig-core

```properties
# Voeg toe aan tenant properties voor H2 dev modus
spring.h2.console.enabled=true
spring.h2.console.path=/h2-console
spring.h2.console.settings.web-allow-others=true

# URL na opstart:
# http://localhost:80/phr-globalconfig-core-backend/h2-console
# JDBC URL: jdbc:h2:mem:gccore_cspayrollhr
```

---

## 9. Verificatie

### 9.1 Complete health check script

Sla op als `C:\Users\kvo\Desktop\local-dev\health-check.ps1`:

```powershell
#!/usr/bin/env pwsh
# health-check.ps1 — Controleer alle lokale services

$services = @(
    @{ Name = "Keycloak";             Url = "http://localhost:8080/health/ready" },
    @{ Name = "phr-globalconfig-core"; Url = "http://localhost:80/phr-globalconfig-core-backend/actuator/health" },
    @{ Name = "WCS Backend";          Url = "http://localhost:58082/actuator/health" },
    @{ Name = "phr-globalconfig BE";  Url = "http://localhost:8090/actuator/health" },  # pas poort aan
    @{ Name = "WCS Portal";           Url = "http://localhost:4200" },
    @{ Name = "phr-globalconfig FE";  Url = "http://localhost:54210" }
)

Write-Host "`n=== SERVICE HEALTH CHECK ===" -ForegroundColor Cyan
Write-Host "Tijdstip: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $status = if ($response.StatusCode -eq 200) { "✅ UP" } else { "⚠️  HTTP $($response.StatusCode)" }
        Write-Host "$($service.Name.PadRight(30)) $status" -ForegroundColor Green
    } catch {
        Write-Host "$($service.Name.PadRight(30)) ❌ DOWN ($_)" -ForegroundColor Red
    }
}

Write-Host "`n=== DOCKER CONTAINERS ===" -ForegroundColor Cyan
docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"

Write-Host "`n=== MARIADB DATABASES ===" -ForegroundColor Cyan
docker exec local-mariadb mariadb -u root -prootpassword -e "SHOW DATABASES;" 2>$null
```

```powershell
# Uitvoeren:
pwsh C:\Users\kvo\Desktop\local-dev\health-check.ps1
```

### 9.2 Keycloak verificatie

```powershell
# Realm bestaat
Invoke-WebRequest "http://localhost:8080/realms/cspayrollhr" | ConvertFrom-Json | Select-Object realm

# OpenID Configuration
Invoke-WebRequest "http://localhost:8080/realms/cspayrollhr/.well-known/openid-configuration" | ConvertFrom-Json
```

### 9.3 Test token ophalen

```powershell
# Haal een JWT token op (Direct Access Grant)
$body = @{
    grant_type = "password"
    client_id  = "wcs-portal"
    username   = "admin-local"
    password   = "admin"
}

$response = Invoke-RestMethod `
    -Method POST `
    -Uri "http://localhost:8080/realms/cspayrollhr/protocol/openid-connect/token" `
    -Body $body `
    -ContentType "application/x-www-form-urlencoded"

$token = $response.access_token
Write-Host "Token ontvangen (eerste 50 tekens): $($token.Substring(0, [Math]::Min(50, $token.Length)))..."

# Test authenticated call naar WCS
Invoke-RestMethod `
    -Uri "http://localhost:58082/api/v1/health" `  # pas endpoint aan
    -Headers @{ Authorization = "Bearer $token" }
```

### 9.4 Swagger / OpenAPI endpoints

| Service | Swagger URL |
|---------|-------------|
| WCS Backend | `http://localhost:58082/swagger-ui.html` |
| phr-globalconfig-core | `http://localhost:80/phr-globalconfig-core-backend/swagger-ui.html` |
| phr-globalconfig BE | `http://localhost:8090/swagger-ui.html` (pas poort aan) |

### 9.5 MariaDB verificatie

```powershell
# Via Docker
docker exec -it local-mariadb mariadb -u wcs_user -pwcs_password wcs_local -e "SHOW TABLES;"

# Liquibase changelog controleren
docker exec -it local-mariadb mariadb -u wcs_user -pwcs_password wcs_local `
  -e "SELECT ID, AUTHOR, FILENAME, DATEEXECUTED FROM DATABASECHANGELOG ORDER BY DATEEXECUTED DESC LIMIT 10;"
```

---

## 10. Docker Compose Voorbeeld

Sla op als `C:\Users\kvo\Desktop\local-dev\docker-compose.local.yml`:

```yaml
# docker-compose.local.yml
# Lokale development infrastructure voor WCS + PHR GlobalConfig + LIMA
# Gebruik: docker compose -f docker-compose.local.yml up -d

version: '3.8'

networks:
  local-dev:
    driver: bridge
    name: local-dev-network

volumes:
  mariadb_data:
    name: local_mariadb_data
  keycloak_data:
    name: local_keycloak_data

services:

  # =========================================================
  # MariaDB 10.x
  # Poort: 53306 (niet-standaard, conform WCS configuratie)
  # =========================================================
  mariadb:
    image: mariadb:10.11
    container_name: local-mariadb
    restart: unless-stopped
    networks:
      - local-dev
    ports:
      - "53306:3306"
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: wcs_local
      MYSQL_USER: wcs_user
      MYSQL_PASSWORD: wcs_password
      TZ: Europe/Brussels
    volumes:
      - mariadb_data:/var/lib/mysql
      - ./mariadb-init:/docker-entrypoint-initdb.d:ro
    command: >
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --default-time-zone='+01:00'
      --innodb-buffer-pool-size=256M
      --max-connections=100
    healthcheck:
      test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
      start_period: 30s
      interval: 10s
      timeout: 5s
      retries: 5

  # =========================================================
  # Keycloak 24.x
  # Poort: 8080
  # Realm: cspayrollhr (handmatig aanmaken of via import)
  # =========================================================
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: local-keycloak
    restart: unless-stopped
    networks:
      - local-dev
    ports:
      - "8080:8080"
    environment:
      KC_DB: dev-mem          # In-memory voor snelle lokale dev
      # KC_DB: mariadb        # Uncomment voor persistente Keycloak data
      # KC_DB_URL: jdbc:mariadb://mariadb:3306/keycloak
      # KC_DB_USERNAME: keycloak_user
      # KC_DB_PASSWORD: keycloak_password
      KC_BOOTSTRAP_ADMIN_USERNAME: admin
      KC_BOOTSTRAP_ADMIN_PASSWORD: admin
      KC_HTTP_ENABLED: "true"
      KC_HOSTNAME_STRICT: "false"
      KC_HOSTNAME_STRICT_HTTPS: "false"
      KC_LOG_LEVEL: INFO
    command: start-dev
    volumes:
      - ./keycloak-realm:/opt/keycloak/data/import:ro
      # Uncomment om realm automatisch te importeren:
      # command: start-dev --import-realm
    healthcheck:
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/localhost/8080; echo -e 'GET /health/ready HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n' >&3; grep -q '\"status\": \"UP\"' <&3"]
      start_period: 60s
      interval: 15s
      timeout: 10s
      retries: 5
    depends_on:
      mariadb:
        condition: service_healthy

  # =========================================================
  # Adminer — Web UI voor database beheer
  # Poort: 9090
  # =========================================================
  adminer:
    image: adminer:latest
    container_name: local-adminer
    restart: unless-stopped
    networks:
      - local-dev
    ports:
      - "9090:8080"
    environment:
      ADMINER_DEFAULT_SERVER: mariadb
      ADMINER_DESIGN: pepa-linha
    depends_on:
      - mariadb
```

### MariaDB initialisatie script

Maak de map `mariadb-init/` aan naast je `docker-compose.local.yml`:

```powershell
New-Item -ItemType Directory -Path "C:\Users\kvo\Desktop\local-dev\mariadb-init" -Force
```

Sla op als `C:\Users\kvo\Desktop\local-dev\mariadb-init\01-init-databases.sql`:

```sql
-- 01-init-databases.sql
-- Wordt uitgevoerd bij eerste start van de MariaDB container

-- GlobalConfig Core database
CREATE DATABASE IF NOT EXISTS globalconfig_core
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'gccore_user'@'%' IDENTIFIED BY 'gccore_password';
GRANT ALL PRIVILEGES ON globalconfig_core.* TO 'gccore_user'@'%';

-- GlobalConfig database
CREATE DATABASE IF NOT EXISTS globalconfig
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'globalconfig_user'@'%' IDENTIFIED BY 'globalconfig_password';
GRANT ALL PRIVILEGES ON globalconfig.* TO 'globalconfig_user'@'%';

-- Keycloak database (optioneel, voor persistente Keycloak data)
-- CREATE DATABASE IF NOT EXISTS keycloak
--   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- CREATE USER IF NOT EXISTS 'keycloak_user'@'%' IDENTIFIED BY 'keycloak_password';
-- GRANT ALL PRIVILEGES ON keycloak.* TO 'keycloak_user'@'%';

FLUSH PRIVILEGES;
```

### Handige Docker commando's

```powershell
# Start alles
docker compose -f docker-compose.local.yml up -d

# Stop alles (behoud data)
docker compose -f docker-compose.local.yml stop

# Stop en verwijder containers (behoud volumes)
docker compose -f docker-compose.local.yml down

# VOLLEDIGE RESET (verwijder ook data volumes!)
docker compose -f docker-compose.local.yml down -v

# Logs bekijken
docker compose -f docker-compose.local.yml logs -f

# Specifieke service herstarten
docker compose -f docker-compose.local.yml restart keycloak

# Container status
docker compose -f docker-compose.local.yml ps
```

---

## Samenvatting Poortenoverzicht

| Service | Host Poort | Container Poort | Beschrijving |
|---------|-----------|-----------------|--------------|
| MariaDB | `53306` | `3306` | WCS + GlobalConfig databases |
| Keycloak | `8080` | `8080` | OAuth2 / OIDC server |
| Adminer | `9090` | `8080` | Database web UI |
| phr-globalconfig-core | `80` | — | Spring Boot microservice |
| WCS Backend | `58082` | — | Spring Boot multi-module |
| phr-globalconfig FE | `54210` | — | Angular dev server |
| WCS Portal | `4200` | — | Angular SPA |

---

## Cheat Sheet — Dagelijkse Opstart

```powershell
# === STAP 1: Docker infrastructure ===
cd C:\Users\kvo\Desktop\local-dev
docker compose -f docker-compose.local.yml up -d
Start-Sleep -Seconds 60  # Wacht op Keycloak

# === STAP 2: phr-globalconfig-core ===
cd C:\Users\kvo\Desktop\phr-globalconfig-core-develop
$env:MULTITENANT_CONFIG_LOCATION = "backend\config"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; .\gradlew bootRun --args='--spring.profiles.active=dev,h2'"

# === STAP 3: WCS Backend ===
cd C:\Users\kvo\Desktop\wcs-backend-develop
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; java -jar wcs-backend\target\wcs-backend-*.jar --spring.profiles.active=default,local"

# === STAP 4: phr-globalconfig ===
cd C:\Users\kvo\Desktop\phr-globalconfig-develop
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; .\gradlew bootRun"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd\frontend'; npm start"

# === STAP 5: WCS Portal ===
cd C:\Users\kvo\Desktop\wcs-portal-develop\frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$pwd'; npm start"

# === Verificatie ===
Start-Sleep -Seconds 30
pwsh C:\Users\kvo\Desktop\local-dev\health-check.ps1
```

---

*Document gegenereerd voor VorstersNV ontwikkelomgeving — Cipal Schaubroeck PayrollHR integratie*
