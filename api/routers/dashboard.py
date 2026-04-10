"""
VorstersNV Dashboard API Router
KPI-overzichten gevoed vanuit beide databases.
Toegang: admin en tester rollen.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from api.auth.jwt import require_admin_or_tester, TokenData

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
):
    """
    Volledig dashboard in één request.

    Bevat:
    - **KPIs**: omzet, orders, klanten
    - **Top producten**: best verkochte items
    - **Agent scores**: AI-prestaties per agent
    - **Voorraad alerts**: producten met lage voorraad
    - **Omzet trend**: laatste 30 dagen
    """
    return DashboardOverzicht(
        kpis=KPIResponse(
            omzet_vandaag=0, omzet_week=0, omzet_maand=0, omzet_jaar=0,
            orders_vandaag=0, orders_open=0, orders_verzonden=0,
            gemiddelde_orderwaarde=0, nieuwe_klanten_maand=0, retour_percentage=0,
        ),
        top_producten=[],
        agent_scores=[],
        voorraad_alerts=[],
        omzet_trend=[],
    )


@router.get(
    "/kpis",
    response_model=KPIResponse,
    summary="KPI overzicht",
)
async def get_kpis(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    """Haal de kerngetallen op voor het dashboard."""
    return KPIResponse(
        omzet_vandaag=0, omzet_week=0, omzet_maand=0, omzet_jaar=0,
        orders_vandaag=0, orders_open=0, orders_verzonden=0,
        gemiddelde_orderwaarde=0, nieuwe_klanten_maand=0, retour_percentage=0,
    )


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


@router.get(
    "/voorraad-alerts",
    response_model=list[VoorraadAlert],
    summary="Voorraad alerts",
)
async def voorraad_alerts_dashboard(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
):
    """Producten met een voorraad onder de drempelwaarde."""
    return []


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
