"""
VorstersNV – Feedback router (Wave 8 prototype)

Endpoints:
  POST /api/portal/projects/{project_id}/feedback
  GET  /api/portal/projects/{project_id}/feedback
  GET  /api/portal/projects/{project_id}/feedback/summary

Gebruikt een module-level FeedbackStore (in-memory dict) als singleton.
Geen DB dependency nodig in Wave 8; FeedbackRecordModel staat klaar voor Wave 9.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, field_validator

router = APIRouter(tags=["feedback"])


# ── Enums ─────────────────────────────────────────────────────────────────────

class FeedbackSectie(str, Enum):
    KWALITEIT      = "kwaliteit"
    DUIDELIJKHEID  = "duidelijkheid"
    BRUIKBAARHEID  = "bruikbaarheid"
    VOLLEDIGHEID   = "volledigheid"
    AANBEVELINGEN  = "aanbevelingen"


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    agent_name:     str                              # welke agent beoordeeld
    prompt_version: str                              # bijv. "2.1.3"
    ratings:        dict[FeedbackSectie, int]        # sectie → score 1-5
    opmerking:      str | None = None                # vrije tekst
    beoordelaar:    str                              # "klant" | "consultant"
    trace_id:       str | None = None

    @field_validator("ratings")
    @classmethod
    def validate_ratings(cls, v: dict[FeedbackSectie, int]) -> dict[FeedbackSectie, int]:
        for sectie, score in v.items():
            if score < 1 or score > 5:
                raise ValueError(
                    f"Score voor '{sectie}' moet tussen 1 en 5 liggen, niet {score}"
                )
        return v

    @field_validator("beoordelaar")
    @classmethod
    def validate_beoordelaar(cls, v: str) -> str:
        toegestaan = {"klant", "consultant", "auto"}
        if v not in toegestaan:
            raise ValueError(f"beoordelaar moet een van {toegestaan} zijn")
        return v


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feedback_id:      str
    project_id:       str
    agent_name:       str
    prompt_version:   str
    ratings:          dict[str, int]
    gemiddelde_score: float
    opmerking:        str | None
    beoordelaar:      str
    trace_id:         str | None
    aangemaakt_op:    str


class FeedbackSummary(BaseModel):
    project_id:              str
    totaal_beoordelingen:    int
    gemiddelde_per_sectie:   dict[str, float]
    algeheel_gemiddelde:     float
    beste_agent:             str | None
    verbeterpunten:          list[str]   # secties met score < 3.5


# ── In-memory store ───────────────────────────────────────────────────────────

class FeedbackStore:
    """
    Module-level singleton voor Wave 8-prototyping.
    Slaat alle FeedbackResponse-records op in een dict geïndexeerd op project_id.
    """

    def __init__(self) -> None:
        # project_id → list[dict]
        self._store: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(self, project_id: str, record: dict[str, Any]) -> None:
        self._store[project_id].append(record)

    def get_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return list(self._store.get(project_id, []))

    def all_projects(self) -> dict[str, list[dict[str, Any]]]:
        return dict(self._store)


_store = FeedbackStore()


# ── Hulpfuncties ──────────────────────────────────────────────────────────────

def _bereken_gemiddelde(ratings: dict[str, int]) -> float:
    if not ratings:
        return 0.0
    return round(sum(ratings.values()) / len(ratings), 2)


def _record_naar_response(record: dict[str, Any]) -> FeedbackResponse:
    return FeedbackResponse(
        feedback_id=record["feedback_id"],
        project_id=record["project_id"],
        agent_name=record["agent_name"],
        prompt_version=record["prompt_version"],
        ratings=record["ratings"],
        gemiddelde_score=record["gemiddelde_score"],
        opmerking=record["opmerking"],
        beoordelaar=record["beoordelaar"],
        trace_id=record["trace_id"],
        aangemaakt_op=record["aangemaakt_op"],
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sla nieuwe feedback op voor een project",
)
async def create_feedback(
    project_id: str,
    payload: FeedbackCreate,
) -> FeedbackResponse:
    """
    Maak een nieuwe feedbackbeoordeling aan voor het opgegeven project.

    - Valideer dat alle ratings tussen 1 en 5 liggen.
    - Bereken de gemiddelde score over alle secties.
    - Sla op in de in-memory FeedbackStore.
    """
    ratings_str: dict[str, int] = {
        sectie.value: score for sectie, score in payload.ratings.items()
    }
    gemiddelde_score = _bereken_gemiddelde(ratings_str)

    record: dict[str, Any] = {
        "feedback_id":      str(uuid.uuid4()),
        "project_id":       project_id,
        "agent_name":       payload.agent_name,
        "prompt_version":   payload.prompt_version,
        "ratings":          ratings_str,
        "gemiddelde_score": gemiddelde_score,
        "opmerking":        payload.opmerking,
        "beoordelaar":      payload.beoordelaar,
        "trace_id":         payload.trace_id,
        "aangemaakt_op":    datetime.now(timezone.utc).isoformat(),
    }

    _store.add(project_id, record)
    return _record_naar_response(record)


@router.get(
    "/projects/{project_id}/feedback",
    response_model=list[FeedbackResponse],
    summary="Haal alle feedbackbeoordelingen op voor een project",
)
async def get_feedback(project_id: str) -> list[FeedbackResponse]:
    """
    Geeft alle feedbackrecords terug voor het opgegeven project_id.
    Leeg resultaat wanneer er nog geen feedback is.
    """
    records = _store.get_for_project(project_id)
    return [_record_naar_response(r) for r in records]


@router.get(
    "/projects/{project_id}/feedback/summary",
    response_model=FeedbackSummary,
    summary="Geaggregeerde feedbacksamenvatting voor een project",
)
async def get_feedback_summary(project_id: str) -> FeedbackSummary:
    """
    Aggregeert alle feedback voor het project:

    - Gemiddelde score per sectie
    - Algeheel gemiddelde over alle beoordelingen
    - Beste agent (hoogste gemiddelde score)
    - Verbeterpunten: secties waarvan het gemiddelde onder de 3,5 ligt
    """
    records = _store.get_for_project(project_id)

    if not records:
        return FeedbackSummary(
            project_id=project_id,
            totaal_beoordelingen=0,
            gemiddelde_per_sectie={},
            algeheel_gemiddelde=0.0,
            beste_agent=None,
            verbeterpunten=[],
        )

    # ── Gemiddelde per sectie ────────────────────────────────────────────────
    sectie_scores: dict[str, list[int]] = defaultdict(list)
    for record in records:
        for sectie, score in record["ratings"].items():
            sectie_scores[sectie].append(score)

    gemiddelde_per_sectie: dict[str, float] = {
        sectie: round(sum(scores) / len(scores), 2)
        for sectie, scores in sectie_scores.items()
    }

    # ── Algeheel gemiddelde ──────────────────────────────────────────────────
    alle_scores = [
        score
        for record in records
        for score in record["ratings"].values()
    ]
    algeheel_gemiddelde = round(sum(alle_scores) / len(alle_scores), 2) if alle_scores else 0.0

    # ── Beste agent ──────────────────────────────────────────────────────────
    agent_scores: dict[str, list[float]] = defaultdict(list)
    for record in records:
        agent_scores[record["agent_name"]].append(record["gemiddelde_score"])

    beste_agent: str | None = None
    if agent_scores:
        beste_agent = max(
            agent_scores,
            key=lambda agent: sum(agent_scores[agent]) / len(agent_scores[agent]),
        )

    # ── Verbeterpunten (gemiddelde < 3,5) ────────────────────────────────────
    verbeterpunten = [
        sectie
        for sectie, gem in gemiddelde_per_sectie.items()
        if gem < 3.5
    ]

    return FeedbackSummary(
        project_id=project_id,
        totaal_beoordelingen=len(records),
        gemiddelde_per_sectie=gemiddelde_per_sectie,
        algeheel_gemiddelde=algeheel_gemiddelde,
        beste_agent=beste_agent,
        verbeterpunten=verbeterpunten,
    )
