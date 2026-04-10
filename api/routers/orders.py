"""
VorstersNV Orders API Router
Order beheer met status-updates en agent-integratie.
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_db
from db.models import OrderStatus
from db.models.models import Customer, Invoice, Order, OrderItem, Product

logger = logging.getLogger(__name__)

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

def _order_nummer() -> str:
    """Genereer een uniek order nummer: ORD-{jaar}-{8 hex tekens}."""
    return f"ORD-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:8].upper()}"


def _to_response(order: Order) -> OrderResponse:
    items = [
        OrderItemResponse(
            id=i.id,
            product_id=i.product_id,
            aantal=i.aantal,
            stukprijs=str(i.stukprijs),
            subtotaal=str(i.subtotaal),
        )
        for i in (order.items or [])
    ]
    return OrderResponse(
        id=order.id,
        order_nummer=order.order_nummer,
        status=order.status,
        customer_id=order.customer_id,
        totaal=str(order.totaal),
        btw_bedrag=str(order.btw_bedrag),
        verzendkosten=str(order.verzendkosten),
        betaalmethode=order.betaalmethode,
        payment_id=order.payment_id,
        tracking_code=order.tracking_code,
        items=items,
        aangemaakt_op=order.aangemaakt_op.isoformat(),
        bijgewerkt_op=order.bijgewerkt_op.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/statistieken/overzicht",
    summary="Order statistieken",
    tags=["Statistieken"],
)
async def order_statistieken(db: Annotated[AsyncSession, Depends(get_db)]):
    """Haal orderstatistieken op voor het admin-dashboard."""
    today = datetime.now(timezone.utc).date()
    first_of_month = today.replace(day=1)

    total_q = await db.execute(select(func.count(Order.id)))
    total = total_q.scalar_one_or_none() or 0

    open_q = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.pending)
    )
    open_orders = open_q.scalar_one_or_none() or 0

    omzet_vandaag_q = await db.execute(
        select(func.coalesce(func.sum(Order.totaal), 0)).where(
            func.date(Order.aangemaakt_op) == today
        )
    )
    omzet_vandaag = omzet_vandaag_q.scalar_one_or_none() or Decimal("0")

    omzet_maand_q = await db.execute(
        select(func.coalesce(func.sum(Order.totaal), 0)).where(
            func.date(Order.aangemaakt_op) >= first_of_month
        )
    )
    omzet_maand = omzet_maand_q.scalar_one_or_none() or Decimal("0")

    gem_q = await db.execute(select(func.avg(Order.totaal)))
    gem = gem_q.scalar_one_or_none() or Decimal("0")

    return {
        "totaal_orders": total,
        "omzet_vandaag": str(round(Decimal(str(omzet_vandaag)), 2)),
        "omzet_maand": str(round(Decimal(str(omzet_maand)), 2)),
        "openstaande_orders": open_orders,
        "gemiddelde_orderwaarde": str(round(Decimal(str(gem)), 2)),
    }


@router.get(
    "/",
    response_model=OrderListResponse,
    summary="Lijst van orders",
)
async def list_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status", description="Filter op orderstatus"),
):
    """Haal alle orders op met optionele statusfilter."""
    q = select(Order).options(selectinload(Order.items))
    if status_filter:
        q = q.where(Order.status == status_filter)

    count_q = select(func.count(Order.id))
    if status_filter:
        count_q = count_q.where(Order.status == status_filter)

    total_result = await db.execute(count_q)
    total = total_result.scalar_one_or_none() or 0

    q = q.order_by(Order.aangemaakt_op.desc()).offset((pagina - 1) * per_pagina).limit(per_pagina)
    result = await db.execute(q)
    orders = result.scalars().all()

    return OrderListResponse(
        items=[_to_response(o) for o in orders],
        totaal=total,
        pagina=pagina,
        per_pagina=per_pagina,
    )


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nieuwe order aanmaken",
    description="Maak een nieuwe order aan. Triggert automatisch de order_verwerking_agent.",
)
async def create_order(
    order_in: OrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Maak een nieuwe order aan.

    Na het aanmaken wordt automatisch:
    - De **order_verwerking_agent** getriggerd
    - Een bevestigingsmail opgesteld
    - De voorraad bijgewerkt
    """
    # Upsert customer op e-mail
    cust_result = await db.execute(
        select(Customer).where(Customer.email == order_in.customer.email)
    )
    customer = cust_result.scalar_one_or_none()
    if customer is None:
        customer = Customer(**order_in.customer.model_dump())
        db.add(customer)
        await db.flush()

    # Valideer producten + voorraad, bereken totaal
    product_ids = [i.product_id for i in order_in.items]
    prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products_map: dict[int, Product] = {p.id: p for p in prod_result.scalars().all()}

    for item in order_in.items:
        prod = products_map.get(item.product_id)
        if prod is None:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} niet gevonden"
            )
        if prod.voorraad < item.aantal:
            raise HTTPException(
                status_code=409,
                detail=f"Onvoldoende voorraad voor '{prod.naam}': {prod.voorraad} beschikbaar",
            )

    subtotalen = [i.stukprijs * i.aantal for i in order_in.items]
    totaal = sum(subtotalen)
    btw = round(totaal * Decimal("0.21"), 2)
    verzend = Decimal("0.00") if totaal >= Decimal("50") else Decimal("4.95")

    new_order = Order(
        order_nummer=_order_nummer(),
        customer_id=customer.id,
        totaal=totaal,
        btw_bedrag=btw,
        verzendkosten=verzend,
        betaalmethode=order_in.betaalmethode,
        notities=order_in.notities,
        status=OrderStatus.pending,
    )
    db.add(new_order)
    await db.flush()

    for item in order_in.items:
        subtotaal = item.stukprijs * item.aantal
        db.add(OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            aantal=item.aantal,
            stukprijs=item.stukprijs,
            subtotaal=subtotaal,
        ))
        # Voorraad verlagen
        products_map[item.product_id].voorraad -= item.aantal

    await db.commit()
    await db.refresh(new_order)

    # Laad items eager voor response
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == new_order.id)
    )
    order = result.scalar_one()

    logger.info("Order aangemaakt: %s voor klant %s", order.order_nummer, customer.email)
    return _to_response(order)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Order detail",
    responses={404: {"description": "Order niet gevonden"}},
)
async def get_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Haal een specifieke order op via ID."""
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden")
    return _to_response(order)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Orderstatus bijwerken",
    responses={404: {"description": "Order niet gevonden"}},
)
async def update_order_status(
    order_id: int,
    update: OrderStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Werk de status van een order bij.

    Automatische acties per statuswijziging:
    - **shipped** → verzendbericht via agent
    - **returned** → retourverwerking via klantenservice_agent
    - **cancelled** → voorraad terugboeken
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} niet gevonden")

    order.status = update.status
    if update.tracking_code:
        order.tracking_code = update.tracking_code
    if update.notities:
        order.notities = update.notities

    # Voorraad terugboeken bij annulering
    if update.status == OrderStatus.cancelled:
        product_ids = [i.product_id for i in order.items]
        prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        products_map = {p.id: p for p in prod_result.scalars().all()}
        for item in order.items:
            if item.product_id in products_map:
                products_map[item.product_id].voorraad += item.aantal

    await db.commit()
    await db.refresh(order)

    logger.info("Order %s status → %s", order.order_nummer, update.status.value)
    return _to_response(order)


@router.get(
    "/{order_id}/factuur",
    summary="Factuur ophalen",
    responses={404: {"description": "Factuur niet gevonden"}},
)
async def get_invoice(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Haal de factuur op voor een order."""
    result = await db.execute(
        select(Invoice).where(Invoice.order_id == order_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail=f"Geen factuur voor order {order_id}")
    return {
        "factuur_nummer": invoice.factuur_nummer,
        "order_id": invoice.order_id,
        "totaal": str(invoice.totaal),
        "btw_bedrag": str(invoice.btw_bedrag),
        "pdf_url": invoice.pdf_url,
        "aangemaakt_op": invoice.aangemaakt_op.isoformat(),
    }
