"""
VorstersNV Betalingen Router — DB-backed implementatie.
Bestelling aanmaken persisteert in PostgreSQL via Order/Customer/OrderItem modellen.
Betaal-URL is mock totdat b3 (Mollie-integratie) live gaat.
"""
import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.auth.jwt import TokenData, get_optional_user
from api.config import settings
from db.database import get_db
from db.models import Customer, Order, OrderItem, OrderStatus, Product

router = APIRouter()

BTW_PERCENTAGE = Decimal("0.21")
BASE_URL = settings.base_url


# ── Schemas ───────────────────────────────────────────────────────────────────

class CartItem(BaseModel):
    product_id: int
    naam: str
    prijs: Decimal
    aantal: int


class BestellingAanmakenRequest(BaseModel):
    items: list[CartItem]
    klant_naam: str = Field(..., example="Koen Vorster")
    klant_email: str = Field(..., example="koen@vorstersNV.be")
    klant_adres: str = Field(..., example="Antwerpsesteenweg 1")
    klant_stad: str = Field(..., example="Mechelen")
    klant_postcode: str = Field(..., example="2800")
    klant_land: str = Field("BE", example="BE")
    opmerking: str | None = None


class BestellingResponse(BaseModel):
    bestelling_id: str
    status: str
    totaal_excl: Decimal
    btw: Decimal
    totaal_incl: Decimal
    betaal_url: str
    aangemaakt_op: str


class BetalingStatusResponse(BaseModel):
    bestelling_id: str
    betaling_id: str
    status: str
    bedrag: Decimal
    methode: str
    aangemaakt_op: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/bestellingen",
    response_model=BestellingResponse,
    status_code=201,
    summary="Bestelling aanmaken + betaallink ophalen",
    description="Maakt een DB-persistente bestelling aan en geeft een betaallink terug. "
                "In productie: Mollie checkout URL (zie b3-mollie-integratie).",
)
async def bestelling_aanmaken(
    body: BestellingAanmakenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[TokenData | None, Depends(get_optional_user)] = None,
):
    # Als de gebruiker ingelogd is, gebruik JWT-email (spoof-safe) en naam
    if current_user is not None:
        body = body.model_copy(update={
            "klant_email": current_user.email,
            "klant_naam": current_user.naam,
        })
    # Valideer producten en voorraad via DB (gebruik DB-prijzen, niet client-prijzen)
    product_ids = [i.product_id for i in body.items]
    prod_result = await db.execute(
        select(Product).where(Product.id.in_(product_ids), Product.actief == True)  # noqa: E712
    )
    products_map: dict[int, Product] = {p.id: p for p in prod_result.scalars().all()}

    problemen: list[str] = []
    for item in body.items:
        prod = products_map.get(item.product_id)
        if prod is None:
            problemen.append(f"Product {item.product_id} niet gevonden of niet actief")
        elif prod.voorraad < item.aantal:
            problemen.append(
                f"'{prod.naam}': slechts {prod.voorraad} op voorraad (gevraagd: {item.aantal})"
            )
    if problemen:
        raise HTTPException(status_code=422, detail={"voorraad_problemen": problemen})

    # Bereken totalen op basis van DB-prijzen (veilig tegen client-side manipulatie)
    excl = sum(products_map[i.product_id].prijs * i.aantal for i in body.items)
    btw = (excl * BTW_PERCENTAGE).quantize(Decimal("0.01"))
    incl = excl + btw
    verzend = Decimal("0.00") if excl >= Decimal("50") else Decimal("4.95")

    # Upsert Customer op e-mail
    cust_result = await db.execute(
        select(Customer).where(Customer.email == body.klant_email)
    )
    customer = cust_result.scalar_one_or_none()
    if customer is None:
        customer = Customer(
            naam=body.klant_naam,
            email=body.klant_email,
            straat=body.klant_adres,
            postcode=body.klant_postcode,
            stad=body.klant_stad,
            land=body.klant_land[:2].upper(),
        )
        db.add(customer)
    else:
        customer.naam = body.klant_naam
        customer.straat = body.klant_adres
        customer.postcode = body.klant_postcode
        customer.stad = body.klant_stad
    await db.flush()

    betaling_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
    order_nummer = f"BST-{uuid.uuid4().hex[:8].upper()}"

    order = Order(
        order_nummer=order_nummer,
        customer_id=customer.id,
        totaal=incl,
        btw_bedrag=btw,
        verzendkosten=verzend,
        betaalmethode="mock",
        payment_id=betaling_id,
        notities=body.opmerking,
        status=OrderStatus.pending,
    )
    db.add(order)
    await db.flush()

    for item in body.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            aantal=item.aantal,
            stukprijs=products_map[item.product_id].prijs,
            subtotaal=products_map[item.product_id].prijs * item.aantal,
        ))
        # Reserveer voorraad direct; bij annulering teruggedraaid via simuleer_betaling
        products_map[item.product_id].voorraad -= item.aantal

    await db.commit()

    betaal_url = (
        f"{BASE_URL}/betaling/mock?betaling_id={betaling_id}&bestelling_id={order_nummer}"
    )

    return BestellingResponse(
        bestelling_id=order_nummer,
        status="wacht_op_betaling",
        totaal_excl=excl,
        btw=btw,
        totaal_incl=incl,
        betaal_url=betaal_url,
        aangemaakt_op=order.aangemaakt_op.isoformat(),
    )


@router.get(
    "/bestellingen/{bestelling_id}",
    summary="Bestelling status ophalen",
)
async def bestelling_status(
    bestelling_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.customer))
        .where(Order.order_nummer == bestelling_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Bestelling {bestelling_id} niet gevonden")

    return {
        "bestelling_id": order.order_nummer,
        "betaling_id": order.payment_id,
        "status": order.status.value,
        "klant_naam": order.customer.naam if order.customer else None,
        "klant_email": order.customer.email if order.customer else None,
        "totaal_incl": str(order.totaal),
        "btw": str(order.btw_bedrag),
        "verzendkosten": str(order.verzendkosten),
        "aangemaakt_op": order.aangemaakt_op.isoformat(),
        "items": [
            {
                "product_id": i.product_id,
                "aantal": i.aantal,
                "stukprijs": str(i.stukprijs),
                "subtotaal": str(i.subtotaal),
            }
            for i in (order.items or [])
        ],
    }


@router.post(
    "/betalingen/{betaling_id}/simuleer",
    summary="[MOCK] Betaling simuleren",
    description="Simuleert een Mollie webhook: zet betaling op 'paid' of 'failed'. Alleen voor demo/test.",
)
async def simuleer_betaling(
    betaling_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = Body(..., embed=True, example="paid"),
):
    if status not in ("paid", "failed", "cancelled"):
        raise HTTPException(
            status_code=422,
            detail="Status moet 'paid', 'failed' of 'cancelled' zijn",
        )

    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.payment_id == betaling_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Betaling {betaling_id} niet gevonden")

    if status == "paid":
        order.status = OrderStatus.paid
    elif status in ("failed", "cancelled"):
        order.status = OrderStatus.cancelled
        # Voorraad terugboeken bij annulering/mislukking
        product_ids = [i.product_id for i in order.items]
        prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        products_map = {p.id: p for p in prod_result.scalars().all()}
        for item in order.items:
            if item.product_id in products_map:
                products_map[item.product_id].voorraad += item.aantal

    await db.commit()
    return {
        "betaling_id": betaling_id,
        "status": status,
        "bestelling_id": order.order_nummer,
    }


@router.get(
    "/betalingen/{betaling_id}",
    response_model=BetalingStatusResponse,
    summary="Betaling status ophalen",
)
async def betaling_status(
    betaling_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Order).where(Order.payment_id == betaling_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail=f"Betaling {betaling_id} niet gevonden")

    return BetalingStatusResponse(
        bestelling_id=order.order_nummer,
        betaling_id=betaling_id,
        status=order.status.value,
        bedrag=order.totaal,
        methode=order.betaalmethode or "mock",
        aangemaakt_op=order.aangemaakt_op.isoformat(),
    )

