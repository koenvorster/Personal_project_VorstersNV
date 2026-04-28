# ⚠️ GEARCHIVEERDE BACKEND — NIET MEER ACTIEF

Deze map bevat de **Spring Boot 3.3.5 (Java 21)** backend van VorstersNV.

## Status: VESTIGIEEL

De Spring Boot backend is **niet meer actief** en wordt niet verder ontwikkeld.
De volledige backend-functionaliteit is overgenomen door **FastAPI** in de `api/` map.

## Actieve backend

| Onderdeel | Locatie |
|-----------|---------|
| FastAPI app | `api/main.py` |
| Routers | `api/routers/` (13 routers) |
| Database modellen | `db/models/` |
| Alembic migraties | `db/migrations/` |

## Git archief

De staat vóór archivering is vastgelegd via:
```
git tag archive/spring-boot-backend-v1
```

## Wanneer kan deze map weg?

Zodra de domeinlogica en businessregels volledig zijn gedocumenteerd in `documentatie/`
of geïmplementeerd in FastAPI. Dan kan `backend/` volledig worden verwijderd.
