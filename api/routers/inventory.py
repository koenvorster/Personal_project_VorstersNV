"""
VorstersNV Inventory API Router
Voorraad beheer met automatische low-stock alerts.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.models import Product

logger = logging.getLogger(__name__)

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

def _to_response(product: Product) -> VoorraadResponse:
    laag = product.voorraad <= product.laag_voorraad_drempel
    if product.voorraad == 0:
        stat = "uitverkocht"
    elif laag:
        stat = "laag"
    else:
        stat = "voldoende"
    return VoorraadResponse(
        product_id=product.id,
        product_naam=product.naam,
        huidige_voorraad=product.voorraad,
        drempel=product.laag_voorraad_drempel,
        laag_voorraad=laag,
        status=stat,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/alerts/laag",
    summary="Low-stock alerts",
    description="Haal alle producten op met een voorraad onder de drempelwaarde.",
)
async def low_stock_alerts(db: Annotated[AsyncSession, Depends(get_db)]):
    """Overzicht van alle producten met een te lage voorraad."""
    result = await db.execute(
        select(Product)
        .where(Product.actief.is_(True))
        .where(Product.voorraad <= Product.laag_voorraad_drempel)
        .order_by(Product.voorraad)
    )
    products = result.scalars().all()
    return {
        "alerts": [_to_response(p) for p in products],
        "totaal": len(products),
    }


@router.get(
    "/",
    response_model=VoorraadOverzicht,
    summary="Voorraadoverzicht",
    description="Haal het complete voorraadoverzicht op met low-stock indicatoren.",
)
async def voorraad_overzicht(
    db: Annotated[AsyncSession, Depends(get_db)],
    alleen_laag: bool = Query(False, description="Toon alleen producten met lage voorraad"),
):
    """
    Haal het volledige voorraadoverzicht op.

    - **alleen_laag**: Toon alleen producten onder de drempelwaarde
    """
    q = select(Product).where(Product.actief.is_(True))
    if alleen_laag:
        q = q.where(Product.voorraad <= Product.laag_voorraad_drempel)
    q = q.order_by(Product.naam)

    result = await db.execute(q)
    products = result.scalars().all()

    laag_count = sum(1 for p in products if p.voorraad <= p.laag_voorraad_drempel)

    return VoorraadOverzicht(
        items=[_to_response(p) for p in products],
        totaal_producten=len(products),
        laag_voorraad_aantal=laag_count,
    )


@router.get(
    "/{product_id}",
    response_model=VoorraadResponse,
    summary="Voorraad van één product",
    responses={404: {"description": "Product niet gevonden"}},
)
async def get_voorraad(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Haal de actuele voorraad op voor één product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")
    return _to_response(product)


@router.put(
    "/{product_id}",
    response_model=VoorraadResponse,
    summary="Voorraad instellen",
    description="Stel de exacte voorraad in voor een product.",
)
async def set_voorraad(
    product_id: int,
    update: VoorraadUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Stel de exacte voorraad in.

    Als de nieuwe waarde onder de drempelwaarde valt, wordt automatisch
    een **low-stock alert** gelogged.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} niet gevonden")

    oud = product.voorraad
    product.voorraad = update.nieuw_aantal
    await db.commit()
    await db.refresh(product)

    if update.nieuw_aantal <= product.laag_voorraad_drempel:
        logger.warning(
            "Low-stock alert: %s (voorraad=%d, drempel=%d, reden=%s)",
            product.naam,
            product.voorraad,
            product.laag_voorraad_drempel,
            update.reden or "niet opgegeven",
        )

    logger.info("Voorraad %s: %d → %d (%s)", product.naam, oud, update.nieuw_aantal, update.reden or "-")
    return _to_response(product)


@router.post(
    "/aanpassen",
    response_model=VoorraadResponse,
    summary="Voorraad aanpassen (delta)",
    description="Pas de voorraad aan met een positieve of negatieve waarde.",
)
async def pas_voorraad_aan(
    aanpassing: VoorraadAanpassing,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Pas de voorraad aan met een delta-waarde.

    - Positief getal = voorraad toevoegen (inkoop)
    - Negatief getal = voorraad verminderen (verkoop/uitval)
    """
    result = await db.execute(select(Product).where(Product.id == aanpassing.product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product {aanpassing.product_id} niet gevonden")

    nieuw = product.voorraad + aanpassing.delta
    if nieuw < 0:
        raise HTTPException(
            status_code=409,
            detail=f"Voorraad kan niet negatief worden: huidige={product.voorraad}, delta={aanpassing.delta}",
        )

    oud = product.voorraad
    product.voorraad = nieuw
    await db.commit()
    await db.refresh(product)

    logger.info(
        "Voorraad aangepast %s: %d + %d = %d (%s)",
        product.naam, oud, aanpassing.delta, nieuw, aanpassing.reden or "-",
    )
    return _to_response(product)
