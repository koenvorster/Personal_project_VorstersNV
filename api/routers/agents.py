"""
VorstersNV Agent Analytics API Router
Biedt feedback-statistieken, versie-beheer en interactie-inzichten per AI-agent.
Toegang: admin en tester rollen.
"""
import json
import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.auth.jwt import TokenData, require_admin_or_tester
from ollama.prompt_iterator import PromptIterator

logger = logging.getLogger(__name__)

router = APIRouter()

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"

# Alle operationele agents die feedback kunnen ontvangen
OPERATIONAL_AGENTS = [
    "klantenservice_agent",
    "product_beschrijving_agent",
    "seo_agent",
    "order_verwerking_agent",
    "fraude_detectie_agent",
    "retour_verwerking_agent",
    "voorraad_advies_agent",
]


# ── Schemas ───────────────────────────────────────────────────────────────────

class AgentAnalytics(BaseModel):
    agent_naam: str
    prompt_versie: str
    totaal_interacties: int
    beoordeelde_interacties: int
    gemiddelde_score: float
    lage_scores: int
    verbeter_suggesties: list[str]
    status: str  # "geen_feedback" | "actief"


class InteractieVoorbeeld(BaseModel):
    id: str
    timestamp: str
    prompt_versie: str
    user_input: str
    agent_output: str
    rating: int
    notes: str


class AgentAnalyticsDetail(AgentAnalytics):
    recente_lage_interacties: list[InteractieVoorbeeld]
    score_verdeling: dict[str, int]  # {"1": 3, "2": 5, "3": 10, "4": 20, "5": 15}


class FeedbackRequest(BaseModel):
    rating: int = Field(ge=1, le=5, description="Beoordeling van 1 (slecht) tot 5 (uitstekend)")
    notes: str = Field(default="", description="Optionele toelichting")


class NieuweVersieRequest(BaseModel):
    preprompt: str = Field(min_length=10, description="De nieuwe pre-prompt tekst")
    beschrijving: str = Field(min_length=5, description="Wat is er veranderd?")
    auteur: str = Field(default="admin", description="Wie de versie heeft aangemaakt")


class NieuweVersieResponse(BaseModel):
    versie: str
    agent_naam: str
    bericht: str


class FeedbackResponse(BaseModel):
    success: bool
    interaction_id: str
    bericht: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/analytics",
    response_model=list[AgentAnalytics],
    summary="Analytics overzicht voor alle agents",
    description="Geeft feedback-statistieken terug voor alle operationele AI-agents.",
)
async def alle_agents_analytics(
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
) -> list[AgentAnalytics]:
    return [_agent_analytics(naam) for naam in OPERATIONAL_AGENTS]


@router.get(
    "/analytics/{agent_naam}",
    response_model=AgentAnalyticsDetail,
    summary="Gedetailleerde analytics voor één agent",
)
async def agent_analytics_detail(
    agent_naam: str,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
) -> AgentAnalyticsDetail:
    if agent_naam not in OPERATIONAL_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_naam}' niet gevonden. Geldig: {OPERATIONAL_AGENTS}",
        )

    basis = _agent_analytics(agent_naam)
    lage_interacties = _haal_lage_interacties(agent_naam, max_items=10)
    verdeling = _score_verdeling(agent_naam)

    return AgentAnalyticsDetail(
        **basis.model_dump(),
        recente_lage_interacties=lage_interacties,
        score_verdeling=verdeling,
    )


@router.post(
    "/{agent_naam}/feedback/{interaction_id}",
    response_model=FeedbackResponse,
    summary="Feedback toevoegen aan een interactie",
    status_code=status.HTTP_200_OK,
)
async def voeg_feedback_toe(
    agent_naam: str,
    interaction_id: str,
    feedback: FeedbackRequest,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
) -> FeedbackResponse:
    if agent_naam not in OPERATIONAL_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_naam}' niet gevonden.",
        )

    iterator = PromptIterator(agent_naam)
    ok = iterator.add_feedback(interaction_id, feedback.rating, feedback.notes)

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interactie '{interaction_id}' niet gevonden voor agent '{agent_naam}'.",
        )

    logger.info(
        "Feedback toegevoegd: agent=%s, id=%s, rating=%d",
        agent_naam, interaction_id, feedback.rating,
    )
    return FeedbackResponse(
        success=True,
        interaction_id=interaction_id,
        bericht=f"Feedback (rating {feedback.rating}/5) opgeslagen voor {agent_naam}.",
    )


@router.post(
    "/{agent_naam}/version",
    response_model=NieuweVersieResponse,
    summary="Nieuwe prompt-versie aanmaken",
    status_code=status.HTTP_201_CREATED,
)
async def maak_nieuwe_versie(
    agent_naam: str,
    request: NieuweVersieRequest,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
) -> NieuweVersieResponse:
    if agent_naam not in OPERATIONAL_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_naam}' niet gevonden.",
        )

    iterator = PromptIterator(agent_naam)
    nieuwe_versie = iterator.create_new_version(
        new_preprompt=request.preprompt,
        change_description=request.beschrijving,
        author=request.auteur,
    )

    logger.info(
        "Nieuwe versie %s aangemaakt voor agent '%s' door %s",
        nieuwe_versie, agent_naam, request.auteur,
    )
    return NieuweVersieResponse(
        versie=nieuwe_versie,
        agent_naam=agent_naam,
        bericht=f"Versie {nieuwe_versie} is actief voor {agent_naam}.",
    )


@router.get(
    "/{agent_naam}/interactions",
    summary="Alle interacties voor een agent ophalen",
    description="Geeft een lijst van interacties terug, optioneel gefilterd op max. rating.",
)
async def agent_interacties(
    agent_naam: str,
    current_user: Annotated[TokenData, Depends(require_admin_or_tester)],
    max_rating: int | None = None,
    limiet: int = 20,
) -> list[dict]:
    if agent_naam not in OPERATIONAL_AGENTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_naam}' niet gevonden.",
        )

    log_dir = LOGS_DIR / agent_naam
    if not log_dir.exists():
        return []

    interacties = []
    for log_file in sorted(log_dir.glob("*.json"), reverse=True)[:limiet * 2]:
        try:
            entry = json.loads(log_file.read_text(encoding="utf-8"))
            if max_rating is not None:
                feedback = entry.get("feedback")
                if not feedback or feedback.get("rating", 99) > max_rating:
                    continue
            interacties.append(entry)
            if len(interacties) >= limiet:
                break
        except (json.JSONDecodeError, KeyError):
            continue

    return interacties


# ── Private helpers ───────────────────────────────────────────────────────────

def _agent_analytics(agent_naam: str) -> AgentAnalytics:
    """Bereken analytics voor één agent via PromptIterator."""
    iterator = PromptIterator(agent_naam)
    analyse = iterator.analyse_feedback()

    if analyse.get("status") == "geen_feedback":
        return AgentAnalytics(
            agent_naam=agent_naam,
            prompt_versie=iterator.get_current_version(),
            totaal_interacties=analyse.get("totaal_interacties", 0),
            beoordeelde_interacties=0,
            gemiddelde_score=0.0,
            lage_scores=0,
            verbeter_suggesties=[],
            status="geen_feedback",
        )

    return AgentAnalytics(
        agent_naam=agent_naam,
        prompt_versie=analyse.get("prompt_versie", "1.0"),
        totaal_interacties=analyse.get("totaal_interacties", 0),
        beoordeelde_interacties=analyse.get("beoordeelde_interacties", 0),
        gemiddelde_score=analyse.get("gemiddelde_score", 0.0),
        lage_scores=analyse.get("lage_scores", 0),
        verbeter_suggesties=analyse.get("verbeter_suggesties", []),
        status="actief",
    )


def _haal_lage_interacties(
    agent_naam: str,
    max_rating: int = 2,
    max_items: int = 10,
) -> list[InteractieVoorbeeld]:
    """Haal recent laag beoordeelde interacties op (rating <= max_rating)."""
    log_dir = LOGS_DIR / agent_naam
    if not log_dir.exists():
        return []

    lage = []
    for log_file in sorted(log_dir.glob("*.json"), reverse=True):
        if len(lage) >= max_items:
            break
        try:
            entry = json.loads(log_file.read_text(encoding="utf-8"))
            feedback = entry.get("feedback")
            if feedback and feedback.get("rating", 99) <= max_rating:
                lage.append(InteractieVoorbeeld(
                    id=entry["id"],
                    timestamp=entry["timestamp"],
                    prompt_versie=entry.get("prompt_version", "1.0"),
                    user_input=entry.get("user_input", "")[:200],
                    agent_output=entry.get("agent_output", "")[:300],
                    rating=feedback["rating"],
                    notes=feedback.get("notes", ""),
                ))
        except (json.JSONDecodeError, KeyError):
            continue

    return lage


def _score_verdeling(agent_naam: str) -> dict[str, int]:
    """Tel hoeveel interacties elke score hebben (1 t/m 5)."""
    log_dir = LOGS_DIR / agent_naam
    verdeling: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    if not log_dir.exists():
        return verdeling

    for log_file in log_dir.glob("*.json"):
        try:
            entry = json.loads(log_file.read_text(encoding="utf-8"))
            feedback = entry.get("feedback")
            if feedback and feedback.get("rating") is not None:
                key = str(int(feedback["rating"]))
                if key in verdeling:
                    verdeling[key] += 1
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    return verdeling
