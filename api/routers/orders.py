"""
VorstersNV Orders API Router
Order beheer met status-updates en agent-integratie.
"""
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from db.models import OrderStatus

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class OrderItemIn(BaseModel):
    product_id: int
    aantal: int = Field(..., ge=1)
    stukprijs: Decimal = Field(..., gt=0)


class CustomerIn(BaseModel):
    naam: str = Field(..., example="Jan Janssen")
    email: str = Field(..., example="jan@voorbeeld.nl")
    telefoon: str | None = None
    straat: str | None = None
    postcode: str | None = None
    stad: str | None = None
    land: str = Field("NL", max_length=2)


class OrderCreate(BaseModel):
    customer: CustomerIn
    items: list[OrderItemIn] = Field(..., min_length=1)
    betaalmethode: str | None = Field(None, example="ideal")
    notities: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tracking_code: str | None = None
    notities: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    aantal: int
    stukprijs: str
    subtotaal: str


class OrderResponse(BaseModel):
    id: int
    order_nummer: str
    status: OrderStatus
    customer_id: int
    totaal: str
    btw_bedrag: str
    verzendkosten: str
    betaalmethode: str | None
    payment_id: str | None
    tracking_code: str | None
    items: list[OrderItemResponse]
    aangemaakt_op: str
    bijgewerkt_op: str

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    totaal: int
    pagina: int
    per_pagina: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Lijst van orders",
)
async def list_orders(
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status", description="Filter op orderstatus"),
):
    """Haal alle orders op met optionele statusfilter."""
    return OrderListResponse(items=[], totaal=0, pagina=pagina, per_pagina=per_pagina)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Order detail",
    responses={404: {"description": "Order niet gevonden"}},
)
async def get_order(order_id: int):
    """Haal een specifieke order op via ID."""
    raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden")


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nieuwe order aanmaken",
    description="Maak een nieuwe order aan. Triggert automatisch de order_verwerking_agent.",
)
async def create_order(order: OrderCreate):
    """
    Maak een nieuwe order aan.

    Na het aanmaken wordt automatisch:
    - De **order_verwerking_agent** getriggerd
    - Een bevestigingsmail opgesteld
    - De voorraad bijgewerkt
    """
    raise HTTPException(status_code=501, detail="Database nog niet verbonden – start docker-compose up")


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Orderstatus bijwerken",
    responses={404: {"description": "Order niet gevonden"}},
)
async def update_order_status(order_id: int, update: OrderStatusUpdate):
    """
    Werk de status van een order bij.

    Automatische acties per statuswijziging:
    - **shipped** → verzendbericht via agent
    - **returned** → retourverwerking via klantenservice_agent
    - **cancelled** → voorraad terugboeken
    """
    raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden")


@router.get(
    "/{order_id}/factuur",
    summary="Factuur ophalen",
    responses={404: {"description": "Factuur niet gevonden"}},
)
async def get_invoice(order_id: int):
    """Haal de factuur op voor een order."""
    raise HTTPException(status_code=404, detail=f"Geen factuur voor order {order_id}")


@router.get(
    "/statistieken/overzicht",
    summary="Order statistieken",
    tags=["Statistieken"],
)
async def order_statistieken():
    """Haal orderstatistieken op voor het admin-dashboard."""
    return {
        "totaal_orders": 0,
        "omzet_vandaag": "0.00",
        "omzet_maand": "0.00",
        "openstaande_orders": 0,
        "gemiddelde_orderwaarde": "0.00",
    }
