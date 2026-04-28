"""
VorstersNV API – Hoofdapplicatie
FastAPI met Swagger UI, CORS en alle routers.
"""
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings as _settings
from api.routers import (
    agents,
    ai_platform,
    betalingen,
    dashboard,
    feedback,
    inventory,
    leads,
    logs,
    notifications,
    orders,
    portal,
    products,
    streaming,
)
from api.routers import auth as auth_router

_app_start_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Applicatie-lifecycle: initialiseer services bij opstart, ruim op bij afsluiten."""
    global _app_start_time
    _app_start_time = time.time()

    # Initialiseer log buffer
    from api.routers.logs import setup_log_buffer
    setup_log_buffer()

    # Laad AgentRunner-singleton (preloadt alle YAML-agents)
    from ollama.agent_runner import get_runner
    app.state.agent_runner = get_runner()

    yield

    # Opruimen bij shutdown (toekomst: sluit DB-pool, HTTP-clients, etc.)
app = FastAPI(
    title="VorstersNV API",
    lifespan=lifespan,
    description="""
## VorstersNV Webshop & Bedrijfsplatform API

Volledige REST API voor de VorstersNV webshop met AI-agent integratie en AI Control Platform.

### Functionaliteit
- 🛍️ **Producten** – catalogusbeheer met AI-gegenereerde beschrijvingen
- 📦 **Orders** – orderverwerking met automatische agent-communicatie
- 📊 **Voorraad** – realtime voorraadbeheer met low-stock alerts
- 🤖 **AI-agents** – Ollama-aangedreven klantenservice en SEO
- 🧠 **AI Platform** – Quality monitoring, decision journal, observability en capability registry

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

# CORS – sta frontend toe (via settings, inclusief dev-poorten)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers registreren
app.include_router(leads.router, prefix="/api", tags=["Leads & Contact"])
app.include_router(products.router, prefix="/api/products", tags=["Producten"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Voorraad"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authenticatie & Rollen"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(betalingen.router, prefix="/api", tags=["Bestellingen & Betalingen"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notificaties"])
app.include_router(agents.router, prefix="/api/agents", tags=["AI Agents & Analytics"])
app.include_router(logs.router, prefix="/api/logs", tags=["Logs"])
app.include_router(ai_platform.router, prefix="/api/ai", tags=["AI Platform"])
app.include_router(streaming.router, prefix="/api/analyse", tags=["Streaming & SSE"])
app.include_router(feedback.router, prefix="/api/portal", tags=["Feedback"])
app.include_router(portal.router)


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
    """Controleer of de API draait. Geeft ook server start-tijd terug voor uptime-berekening."""
    now = time.time()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "started_at": (
            datetime.fromtimestamp(_app_start_time, tz=timezone.utc).isoformat()
            if _app_start_time else None
        ),
        "uptime_seconds": int(now - _app_start_time) if _app_start_time else None,
    }
