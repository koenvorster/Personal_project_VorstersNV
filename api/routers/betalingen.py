"""
VorstersNV Betalingen Router — Mock implementatie voor demo/stakeholder presentatie.
In productie: vervang mock_betaling_aanmaken door echte Mollie API call.
"""
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = os.environ.get("DB_URL", "postgresql+psycopg2://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV")
engine = create_engine(DB_URL, pool_pre_ping=True)

router = APIRouter()

BTW_PERCENTAGE = Decimal("0.21")


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
    klant_land: str = Field("België", example="België")
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


# In-memory mock store voor demo (geen DB nodig voor betalingen in mock-modus)
_mock_betalingen: dict[str, dict] = {}
_mock_bestellingen: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bereken_totalen(items: list[CartItem]) -> tuple[Decimal, Decimal, Decimal]:
    excl = sum(i.prijs * i.aantal for i in items)
    btw = (excl * BTW_PERCENTAGE).quantize(Decimal("0.01"))
    incl = excl + btw
    return excl, btw, incl


def _controleer_voorraad(items: list[CartItem]) -> list[str]:
    """Controleer voorraad in DB; geeft lijst van problemen terug."""
    problemen = []
    with Session(engine) as db:
        for item in items:
            row = db.execute(
                text("SELECT naam, voorraad FROM products WHERE id = :id AND actief = true"),
                {"id": item.product_id}
            ).fetchone()
            if not row:
                problemen.append(f"Product {item.product_id} niet gevonden")
            elif row.voorraad < item.aantal:
                problemen.append(f"'{row.naam}': slechts {row.voorraad} op voorraad (gevraagd: {item.aantal})")
    return problemen


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/bestellingen",
    response_model=BestellingResponse,
    status_code=201,
    summary="Bestelling aanmaken + betaallink ophalen",
    description="Maakt een bestelling aan en geeft een mock-betaallink terug. In productie: Mollie checkout URL.",
)
async def bestelling_aanmaken(body: BestellingAanmakenRequest):
    # Voorraad check
    problemen = _controleer_voorraad(body.items)
    if problemen:
        raise HTTPException(status_code=422, detail={"voorraad_problemen": problemen})

    bestelling_id = f"BST-{uuid.uuid4().hex[:8].upper()}"
    betaling_id = f"PAY-{uuid.uuid4().hex[:10].upper()}"
    excl, btw, incl = _bereken_totalen(body.items)
    nu = datetime.now(timezone.utc).isoformat()

    bestelling = {
        "bestelling_id": bestelling_id,
        "betaling_id": betaling_id,
        "status": "wacht_op_betaling",
        "klant_naam": body.klant_naam,
        "klant_email": body.klant_email,
        "klant_adres": f"{body.klant_adres}, {body.klant_postcode} {body.klant_stad}, {body.klant_land}",
        "items": [i.model_dump() for i in body.items],
        "totaal_excl": str(excl),
        "btw": str(btw),
        "totaal_incl": str(incl),
        "aangemaakt_op": nu,
    }
    _mock_bestellingen[bestelling_id] = bestelling
    _mock_betalingen[betaling_id] = {
        "bestelling_id": bestelling_id,
        "status": "open",
        "bedrag": str(incl),
        "methode": "mock",
        "aangemaakt_op": nu,
    }

    # Mock betaal URL — in productie: Mollie checkout URL
    base_url = os.environ.get("BASE_URL", "http://localhost:3000")
    betaal_url = f"{base_url}/betaling/mock?betaling_id={betaling_id}&bestelling_id={bestelling_id}"

    return BestellingResponse(
        bestelling_id=bestelling_id,
        status="wacht_op_betaling",
        totaal_excl=excl,
        btw=btw,
        totaal_incl=incl,
        betaal_url=betaal_url,
        aangemaakt_op=nu,
    )


@router.get(
    "/bestellingen/{bestelling_id}",
    summary="Bestelling status ophalen",
)
async def bestelling_status(bestelling_id: str):
    b = _mock_bestellingen.get(bestelling_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Bestelling {bestelling_id} niet gevonden")
    return b


@router.post(
    "/betalingen/{betaling_id}/simuleer",
    summary="[MOCK] Betaling simuleren",
    description="Simuleert een Mollie webhook: zet betaling op 'paid' of 'failed'. Alleen voor demo.",
)
async def simuleer_betaling(betaling_id: str, status: str = Body(..., embed=True, example="paid")):
    if status not in ("paid", "failed", "cancelled"):
        raise HTTPException(status_code=422, detail="Status moet 'paid', 'failed' of 'cancelled' zijn")

    betaling = _mock_betalingen.get(betaling_id)
    if not betaling:
        raise HTTPException(status_code=404, detail=f"Betaling {betaling_id} niet gevonden")

    betaling["status"] = status
    bestelling = _mock_bestellingen.get(betaling["bestelling_id"], {})
    if status == "paid":
        bestelling["status"] = "betaald"
        # Voorraad verlagen bij betaald
        items = bestelling.get("items", [])
        with Session(engine) as db:
            for item in items:
                db.execute(
                    text("UPDATE products SET voorraad = voorraad - :aantal WHERE id = :id AND voorraad >= :aantal"),
                    {"aantal": item["aantal"], "id": item["product_id"]}
                )
            db.commit()
    elif status in ("failed", "cancelled"):
        bestelling["status"] = "betaling_mislukt"

    return {"betaling_id": betaling_id, "status": status, "bestelling_id": betaling["bestelling_id"]}


@router.get(
    "/betalingen/{betaling_id}",
    response_model=BetalingStatusResponse,
    summary="Betaling status ophalen",
)
async def betaling_status(betaling_id: str):
    b = _mock_betalingen.get(betaling_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"Betaling {betaling_id} niet gevonden")
    return BetalingStatusResponse(
        bestelling_id=b["bestelling_id"],
        betaling_id=betaling_id,
        status=b["status"],
        bedrag=Decimal(b["bedrag"]),
        methode=b["methode"],
        aangemaakt_op=b["aangemaakt_op"],
    )
