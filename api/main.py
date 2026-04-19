"""
VorstersNV API – Hoofdapplicatie
FastAPI met Swagger UI, CORS en alle routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth as auth_router
from api.routers import agents, betalingen, dashboard, inventory, notifications, orders, products

app = FastAPI(
    title="VorstersNV API",
    description="""
## VorstersNV Webshop & Bedrijfsplatform API

Volledige REST API voor de VorstersNV webshop met AI-agent integratie.

### Functionaliteit
- 🛍️ **Producten** – catalogusbeheer met AI-gegenereerde beschrijvingen
- 📦 **Orders** – orderverwerking met automatische agent-communicatie
- 📊 **Voorraad** – realtime voorraadbeheer met low-stock alerts
- 🤖 **AI-agents** – Ollama-aangedreven klantenservice en SEO

### Authenticatie
Gebruik de `Authorization: Bearer <token>` header voor beveiligde endpoints.
""",
    version="1.0.0",
    contact={
        "name": "VorstersNV",
        "url": "https://vorstersNV.be",
    },
    license_info={
        "name": "Privé – VorstersNV",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS – sta frontend toe
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://vorstersNV.be"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers registreren
app.include_router(products.router, prefix="/api/products", tags=["Producten"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Voorraad"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authenticatie & Rollen"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(betalingen.router, prefix="/api", tags=["Bestellingen & Betalingen"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notificaties"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents & Analytics"])


@app.get("/", tags=["Algemeen"], summary="API Root")
async def root():
    """Welkomstbericht met links naar documentatie."""
    return {
        "naam": "VorstersNV API",
        "versie": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Algemeen"], summary="Health check")
async def health():
    """Controleer of de API draait."""
    from datetime import datetime, timezone
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
