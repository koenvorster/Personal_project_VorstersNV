"""
VorstersNV Inventory API Router
Voorraad beheer met automatische low-stock alerts.
"""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class VoorraadUpdate(BaseModel):
    product_id: int
    nieuw_aantal: int = Field(..., ge=0, description="Nieuwe voorraadwaarde")
    reden: str | None = Field(None, example="Inkoop batch 2025-04")


class VoorraadAanpassing(BaseModel):
    product_id: int
    delta: int = Field(..., description="Positief = toevoegen, negatief = aftrekken")
    reden: str | None = None


class VoorraadResponse(BaseModel):
    product_id: int
    product_naam: str
    huidige_voorraad: int
    drempel: int
    laag_voorraad: bool
    status: str


class VoorraadOverzicht(BaseModel):
    items: list[VoorraadResponse]
    totaal_producten: int
    laag_voorraad_aantal: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=VoorraadOverzicht,
    summary="Voorraadoverzicht",
    description="Haal het complete voorraadoverzicht op met low-stock indicatoren.",
)
async def voorraad_overzicht(
    alleen_laag: bool = Query(False, description="Toon alleen producten met lage voorraad"),
):
    """
    Haal het volledige voorraadoverzicht op.

    - **alleen_laag**: Toon alleen producten onder de drempelwaarde
    """
    return VoorraadOverzicht(items=[], totaal_producten=0, laag_voorraad_aantal=0)


@router.get(
    "/{product_id}",
    response_model=VoorraadResponse,
    summary="Voorraad van één product",
    responses={404: {"description": "Product niet gevonden"}},
)
async def get_voorraad(product_id: int):
    """Haal de actuele voorraad op voor één product."""
    raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")


@router.put(
    "/{product_id}",
    response_model=VoorraadResponse,
    summary="Voorraad instellen",
    description="Stel de exacte voorraad in voor een product. Triggert low-stock alert indien nodig.",
)
async def set_voorraad(product_id: int, update: VoorraadUpdate):
    """
    Stel de exacte voorraad in.

    Als de nieuwe waarde onder de drempelwaarde valt, wordt automatisch
    een **low-stock alert** verstuurd via de order_verwerking_agent.
    """
    raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")


@router.post(
    "/aanpassen",
    response_model=VoorraadResponse,
    summary="Voorraad aanpassen (delta)",
    description="Pas de voorraad aan met een positieve of negatieve waarde.",
)
async def pas_voorraad_aan(aanpassing: VoorraadAanpassing):
    """
    Pas de voorraad aan met een delta-waarde.

    - Positief getal = voorraad toevoegen (inkoop)
    - Negatief getal = voorraad verminderen (verkoop/uitval)
    """
    raise HTTPException(status_code=404, detail=f"Product {aanpassing.product_id} niet gevonden")


@router.get(
    "/alerts/laag",
    summary="Low-stock alerts",
    description="Haal alle producten op met een voorraad onder de drempelwaarde.",
)
async def low_stock_alerts():
    """Overzicht van alle producten met een te lage voorraad."""
    return {"alerts": [], "totaal": 0}
