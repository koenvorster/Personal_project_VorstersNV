# VorstersNV – Projectarchitectuur

## Databases

### 1. Webshop DB (`vorstersNV`) – Operationeel
PostgreSQL 16 op poort **5432**

| Tabel | Beschrijving |
|-------|-------------|
| `products` | Productcatalogus met voorraad en SEO-velden |
| `categories` | Productcategorieën |
| `customers` | Klantgegevens |
| `orders` | Orders met status-lifecycle |
| `order_items` | Orderregels (product + aantal + prijs) |
| `invoices` | Facturen gekoppeld aan orders |
| `users` | Platform-gebruikers met rollen |
| `agent_logs` | AI-agent interacties (input/output/rating) |

### 2. Analytics DB (`vorstersNV_analytics`) – Ster-schema
PostgreSQL 16 op poort **5433**

```
                    ┌─────────────┐
                    │  dim_date   │
                    └──────┬──────┘
                           │
┌──────────────┐   ┌───────┴──────┐   ┌──────────────┐
│ dim_product  ├───┤ sales_facts  ├───┤ dim_customer  │
└──────────────┘   └───────┬──────┘   └──────────────┘
                           │
              ┌────────────┴──────────────┐
              │       dim_agent           │
              └───────────────────────────┘
                           │
              ┌────────────┴──────────────┐
              │  agent_performance_facts  │
              └───────────────────────────┘
```

**Dimensietabellen:**
- `dim_date` – Datumkalender (YYYYMMDD key) met dag/week/maand/kwartaal/jaar
- `dim_product` – Product snapshot (SCD Type 2 – historisch)
- `dim_customer` – Klantsegmenten en geografie
- `dim_agent` – AI-agent + prompt-versie

**Feitentabellen:**
- `sales_facts` – Verkoopfeiten per orderregel
- `agent_performance_facts` – Agent-prestaties per interactie

## Migraties uitvoeren

```bash
# Webshop DB
alembic -c alembic.ini upgrade head

# Analytics DB
alembic -c alembic_analytics.ini upgrade head
```

## Rollenbeheer

| Rol | Toegang |
|-----|---------|
| `admin` | Alle endpoints, gebruikersbeheer, dashboard |
| `klant` | Eigen orders, profiel, webshop |
| `tester` | Lees-toegang + dashboard + agent-test endpoints |

## API Documentatie

Na `docker-compose up -d` en `uvicorn api.main:app --reload --port 8000`:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
