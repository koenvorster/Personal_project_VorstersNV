"""
VorstersNV Dashboard API Router
KPI-overzichten gevoed vanuit beide databases.
Toegang: admin en tester rollen.
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.jwt import TokenData, require_admin_or_tester
from db.database import get_db
from db.models import OrderStatus
from db.models.models import Order, Product

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class KPIResponse(BaseModel):
    omzet_vandaag: float
    omzet_week: float
    omzet_maand: float
    omzet_jaar: float
    orders_vandaag: int
    orders_open: int
    orders_verzonden: int
    gemiddelde_orderwaarde: float
    nieuwe_klanten_maand: int
    retour_percentage: float


class TopProduct(BaseModel):
    product_id: int
    naam: str
    verkocht_aantal: int
    omzet: float
    categorie: str | None


class AgentScore(BaseModel):
    agent_naam: str
    gemiddelde_rating: float
    totaal_interacties: int
    escalatie_percentage: float
    prompt_versie: str


class VoorraadAlert(BaseModel):
    product_id: int
    naam: str
    huidige_voorraad: int
    drempel: int
    urgentie: str  # kritiek / laag / normaal


class OmzetPerPeriode(BaseModel):
    periode: str
    omzet: float
    aantal_orders: int


class DashboardOverzicht(BaseModel):
    kpis: KPIResponse
    top_producten: list[TopProduct]
    agent_scores: list[AgentScore]
    voorraad_alerts: list[VoorraadAlert]
    omzet_trend: list[OmzetPerPeriode]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=DashboardOverzicht,
    summary="Volledig dashboard overzicht",
    description="Haal alle KPIs, trends en alerts op in één call. Vereist admin of tester rol.",
)
async def dashboard_overzicht(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    kpis = await _bereken_kpis(db)
    alerts = await _haal_voorraad_alerts(db)
    return DashboardOverzicht(
        kpis=kpis,
        top_producten=[],
        agent_scores=await _haal_agent_scores(),
        voorraad_alerts=alerts,
        omzet_trend=[],
    )


@router.get(
    "/kpis",
    response_model=KPIResponse,
    summary="KPI overzicht",
)
async def get_kpis(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Haal de kerngetallen op voor het dashboard."""
    return await _bereken_kpis(db)


@router.get(
    "/omzet-trend",
    response_model=list[OmzetPerPeriode],
    summary="Omzettrend per dag/week/maand",
)
async def omzet_trend(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    periode: str = Query("dag", enum=["dag", "week", "maand"], description="Granulariteit van de trend"),
    aantal: int = Query(30, ge=7, le=365, description="Aantal periodes terug"),
):
    """
    Omzettrend over tijd, gevoed vanuit de analytics database (sales_facts).

    - **dag**: laatste N dagen
    - **week**: laatste N weken
    - **maand**: laatste N maanden
    """
    return []


@router.get(
    "/top-producten",
    response_model=list[TopProduct],
    summary="Best verkochte producten",
)
async def top_producten(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    limiet: int = Query(10, ge=1, le=50),
    periode_dagen: int = Query(30, ge=1, le=365),
):
    """Top N best verkochte producten van de afgelopen X dagen (vanuit sales_facts)."""
    return []


@router.get(
    "/agent-scores",
    response_model=list[AgentScore],
    summary="AI-agent prestaties",
)
async def agent_scores(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    """
    Overzicht van AI-agent prestaties.
    Gevoed vanuit agent_performance_facts tabel én de lokale JSON logs.
    """
    return await _haal_agent_scores()


@router.get(
    "/voorraad-alerts",
    response_model=list[VoorraadAlert],
    summary="Voorraad alerts",
)
async def voorraad_alerts_dashboard(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Producten met een voorraad onder de drempelwaarde."""
    return await _haal_voorraad_alerts(db)


@router.get(
    "/omzet-per-categorie",
    summary="Omzet per productcategorie",
)
async def omzet_per_categorie(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    periode_dagen: int = Query(30, ge=1, le=365),
):
    """Omzetverdeling per productcategorie (taartdiagram data)."""
    return {"categorieen": [], "periode_dagen": periode_dagen}


# ── Private helpers ───────────────────────────────────────────────────────────

async def _bereken_kpis(db: AsyncSession) -> KPIResponse:
    today = datetime.now(timezone.utc).date()
    first_of_month = today.replace(day=1)
    first_of_year = today.replace(month=1, day=1)

    async def _omzet(filter_clause) -> float:
        q = await db.execute(
            select(func.coalesce(func.sum(Order.totaal), 0)).where(filter_clause)
        )
        return float(q.scalar_one_or_none() or 0)

    omzet_vandaag = await _omzet(func.date(Order.aangemaakt_op) == today)
    omzet_maand = await _omzet(func.date(Order.aangemaakt_op) >= first_of_month)
    omzet_jaar = await _omzet(func.date(Order.aangemaakt_op) >= first_of_year)

    orders_vandaag_q = await db.execute(
        select(func.count(Order.id)).where(func.date(Order.aangemaakt_op) == today)
    )
    orders_vandaag = orders_vandaag_q.scalar_one_or_none() or 0

    open_q = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.pending)
    )
    orders_open = open_q.scalar_one_or_none() or 0

    shipped_q = await db.execute(
        select(func.count(Order.id)).where(Order.status == OrderStatus.shipped)
    )
    orders_verzonden = shipped_q.scalar_one_or_none() or 0

    gem_q = await db.execute(select(func.avg(Order.totaal)))
    gem = float(gem_q.scalar_one_or_none() or 0)

    return KPIResponse(
        omzet_vandaag=round(omzet_vandaag, 2),
        omzet_week=0.0,
        omzet_maand=round(omzet_maand, 2),
        omzet_jaar=round(omzet_jaar, 2),
        orders_vandaag=orders_vandaag,
        orders_open=orders_open,
        orders_verzonden=orders_verzonden,
        gemiddelde_orderwaarde=round(gem, 2),
        nieuwe_klanten_maand=0,
        retour_percentage=0.0,
    )


async def _haal_voorraad_alerts(db: AsyncSession) -> list[VoorraadAlert]:
    result = await db.execute(
        select(Product)
        .where(Product.actief.is_(True))
        .where(Product.voorraad <= Product.laag_voorraad_drempel)
        .order_by(Product.voorraad)
        .limit(50)
    )
    products = result.scalars().all()
    alerts = []
    for p in products:
        if p.voorraad == 0:
            urgentie = "kritiek"
        elif p.voorraad <= p.laag_voorraad_drempel // 2:
            urgentie = "laag"
        else:
            urgentie = "normaal"
        alerts.append(VoorraadAlert(
            product_id=p.id,
            naam=p.naam,
            huidige_voorraad=p.voorraad,
            drempel=p.laag_voorraad_drempel,
            urgentie=urgentie,
        ))
    return alerts


async def _haal_agent_scores() -> list[AgentScore]:
    from ollama.prompt_iterator import PromptIterator
    scores = []
    for agent_naam in ["klantenservice_agent", "product_beschrijving_agent", "seo_agent", "order_verwerking_agent"]:
        iterator = PromptIterator(agent_naam)
        analyse = iterator.analyse_feedback()
        scores.append(AgentScore(
            agent_naam=agent_naam,
            gemiddelde_rating=analyse.get("gemiddelde_score", 0.0),
            totaal_interacties=analyse.get("totaal_interacties", 0),
            escalatie_percentage=0.0,
            prompt_versie=analyse.get("prompt_versie", "1.0"),
        ))
    return scores
