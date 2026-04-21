# Bounded Contexts — VorstersNV (Source of Truth)

> **Dit is de canonieke bron voor het domain model.**
> Verwijs naar dit bestand vanuit CLAUDE.md, copilot-instructions.md en agent prompts.

## DDD Bounded Contexts

| Context | Aggregates | Routers / Locatie | Status |
|---------|-----------|-------------------|--------|
| **Catalog** | Product, Category | `api/routers/products.py` | ✅ Actief |
| **Orders** | Order, OrderLine | `api/routers/orders.py` | ✅ Actief |
| **Inventory** | StockItem, Warehouse | `api/routers/inventory.py` | ✅ Actief |
| **Customer** | Customer, Address | `api/auth.py` | ✅ Actief |
| **Payments** | Payment, Refund | `api/routers/betalingen.py` | ✅ Actief |
| **Notifications** | Notification | `api/routers/notifications.py` | ✅ Actief |
| **Dashboard** | Metrics | `api/routers/dashboard.py` | ✅ Actief |
| **Consultancy** | AnalysisProject, ClientReport | `scripts/analyse_project.py` | 🆕 Fase 6 |

## Context Map

```
┌─────────────────────────────────────────────────────────────┐
│                     VorstersNV Platform                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Catalog    │    Orders    │   Inventory  │   Customer     │
│  Product     │  Order       │  StockItem   │  Customer      │
│  Category    │  OrderLine   │  Warehouse   │  Address       │
├──────────────┴──────┬───────┴──────────────┴────────────────┤
│                     │         Payments                       │
│                     │  Payment, Refund (Mollie)             │
├─────────────────────┴───────────────────────────────────────┤
│  Notifications │  Dashboard  │  Consultancy (Fase 6)        │
│  Notification  │  Metrics    │  AnalysisProject, Report     │
└─────────────────────────────────────────────────────────────┘
```

## Ubiquitous Language

| Term | Context | Definitie |
|------|---------|-----------|
| `Order` | Orders | Een bevestigde bestelling van een klant |
| `OrderLine` | Orders | Eén productregel in een bestelling |
| `StockItem` | Inventory | Een product in een specifiek warehouse |
| `Payment` | Payments | Een Mollie betalingstransactie |
| `Refund` | Payments | Een terugbetaling via Mollie |
| `AnalysisProject` | Consultancy | Een klantenproject dat geanalyseerd wordt |
| `ClientReport` | Consultancy | Het eindrapport voor een klant |

## Welke agent per context?

| Context | Claude Agent | GitHub Copilot Agent |
|---------|-------------|---------------------|
| Catalog / Orders / Payments | `fastapi-developer` | `@developer` |
| Domain model | `fastapi-developer` | `@ddd-modeler` |
| Database / Migraties | `db-explorer` | `@database-expert` |
| Consultancy tools | `code-analyzer` | `@code-analyzer` |
| Frontend | `nextjs-developer` | `@frontend-specialist` |
