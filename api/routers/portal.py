"""
VorstersNV Portal API Router — Wave 9

Endpoints voor het klantportaal: projectbeheer, statusinzage,
rapportage en kostenschattingen voor consultancy-analyses.
"""
from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.models import ClientProject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portal", tags=["portal"])


# ── Status mapping ───────────────────────────────────────────────────────────

# ClientProjectSpace statussen → portal-statussen
_STATUS_MAP: dict[str, str] = {
    "CREATED":   "draft",
    "SCANNING":  "actief",
    "ANALYSING": "in_analyse",
    "RAPPORT":   "rapport_gereed",
    "DONE":      "gesloten",
    "FAILED":    "gesloten",
}

# Portal-statussen → voortgang in procent
_VOORTGANG_MAP: dict[str, int] = {
    "draft":          0,
    "actief":        20,
    "in_analyse":    60,
    "rapport_gereed": 90,
    "gesloten":     100,
}


# ── Schemas ──────────────────────────────────────────────────────────────────

class ProjectAanmaken(BaseModel):
    """Aanvraag voor een nieuw consultancy analyseproject."""

    model_config = ConfigDict(str_strip_whitespace=True)

    project_naam: str
    klant_naam: str
    klant_email: EmailStr
    project_type: str = "code_analyse"  # code_analyse | bedrijfsproces | security_audit
    beschrijving: str = ""


class ProjectStatus(BaseModel):
    """Voortgang en statusinformatie van een project."""

    model_config = ConfigDict(from_attributes=True)

    project_id: str
    project_naam: str
    klant_naam: str
    status: str          # draft | actief | in_analyse | rapport_gereed | gesloten
    voortgang_percent: int   # 0–100
    geschatte_minuten: int | None
    rapport_beschikbaar: bool
    aangemaakt_op: str
    bijgewerkt_op: str


class KostenSchatting(BaseModel):
    """Schatting van tokens, kosten en duur voor een projecttype."""

    project_type: str
    geschatte_tokens: int
    geschatte_kosten_eur: float
    geschatte_minuten: int
    betrouwbaarheid_percent: int


# ── Hulpfuncties ─────────────────────────────────────────────────────────────

def _to_portal_status(db_status: str) -> str:
    """Vertaal DB-status (CREATED/ANALYSING/…) naar portal-status (draft/…)."""
    return _STATUS_MAP.get(db_status.upper(), "draft")


def _to_project_status(project: ClientProject) -> ProjectStatus:
    """Converteer een ClientProject ORM-rij naar het ProjectStatus schema."""
    portal_status = _to_portal_status(project.status)
    voortgang = _VOORTGANG_MAP.get(portal_status, 0)

    # project_naam, klant_email en beschrijving worden in config_json bewaard
    config: dict = project.config_json or {}
    project_naam: str = config.get("project_naam") or project.klant_naam
    geschatte_minuten: int | None = config.get("geschatte_minuten")

    return ProjectStatus(
        project_id=project.project_id,
        project_naam=project_naam,
        klant_naam=project.klant_naam,
        status=portal_status,
        voortgang_percent=voortgang,
        geschatte_minuten=geschatte_minuten,
        rapport_beschikbaar=project.rapport_pad is not None,
        aangemaakt_op=project.aangemaakt_op.isoformat(),
        bijgewerkt_op=project.bijgewerkt_op.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/projects",
    response_model=ProjectStatus,
    status_code=status.HTTP_201_CREATED,
    summary="Nieuw project aanmaken",
    description="Maak een nieuw consultancy analyseproject aan en registreer het in de database.",
)
async def maak_project_aan(
    project_in: ProjectAanmaken,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectStatus:
    """
    Maak een nieuw project aan.

    - Genereert een unieke project-UUID
    - Registreert via ClientProjectSpace indien beschikbaar
    - Slaat op in de `client_projects` database-tabel
    """
    project_id = str(uuid.uuid4())

    # Gebruik ClientProjectSpace als het beschikbaar is
    try:
        from ollama.client_project_space import ProjectConfig, create_project  # noqa: PLC0415

        space = create_project(
            klant_naam=project_in.klant_naam,
            klant_id=str(project_in.klant_email),
            bronpad=Path("."),
            projecttype=project_in.project_type,
            config=ProjectConfig(),
        )
        project_id = space.project_id
        logger.info("ClientProjectSpace aangemaakt: %s", project_id)
    except Exception as exc:  # pragma: no cover
        logger.warning("ClientProjectSpace niet beschikbaar, gebruik uuid4 fallback: %s", exc)

    config_json: dict = {
        "project_naam": project_in.project_naam,
        "klant_email": str(project_in.klant_email),
        "beschrijving": project_in.beschrijving,
    }

    project = ClientProject(
        project_id=project_id,
        klant_naam=project_in.klant_naam,
        klant_id=str(project_in.klant_email),
        projecttype=project_in.project_type,
        bronpad=".",
        status="CREATED",
        config_json=config_json,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    logger.info(
        "Project aangemaakt: id=%s naam=%s klant=%s type=%s",
        project_id,
        project_in.project_naam,
        project_in.klant_naam,
        project_in.project_type,
    )
    return _to_project_status(project)


@router.get(
    "/projects",
    response_model=list[ProjectStatus],
    summary="Alle projecten ophalen",
)
async def lijst_projecten(
    db: Annotated[AsyncSession, Depends(get_db)],
    klant_email: str | None = Query(None, description="Filter op klant e-mailadres"),
) -> list[ProjectStatus]:
    """
    Haal alle projecten op, gesorteerd op aanmaakdatum (nieuwste eerst).

    Optioneel gefilterd op `klant_email`.
    """
    q = select(ClientProject).order_by(ClientProject.aangemaakt_op.desc())
    if klant_email:
        q = q.where(ClientProject.klant_id == klant_email)

    result = await db.execute(q)
    projects = result.scalars().all()
    return [_to_project_status(p) for p in projects]


@router.get(
    "/projects/{project_id}/status",
    response_model=ProjectStatus,
    summary="Projectstatus ophalen",
    responses={404: {"description": "Project niet gevonden"}},
)
async def get_project_status(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProjectStatus:
    """Haal de huidige status en voortgang van een specifiek project op."""
    result = await db.execute(
        select(ClientProject).where(ClientProject.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} niet gevonden",
        )
    return _to_project_status(project)


@router.get(
    "/projects/{project_id}/rapport",
    summary="Analyserapport ophalen als Markdown",
    responses={404: {"description": "Rapport niet beschikbaar"}},
)
async def get_rapport(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Haal het analyserapport op als Markdown tekst.

    Zoekpad (in volgorde):
    1. `documentatie/analyse/{project_id}/*.md`
    2. `rapport_pad` kolom in de database
    """
    result = await db.execute(
        select(ClientProject).where(ClientProject.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} niet gevonden",
        )

    # 1. Zoek in documentatie/analyse/{project_id}/
    analyse_dir = Path("documentatie") / "analyse" / project_id
    if analyse_dir.exists():
        md_bestanden = sorted(analyse_dir.glob("*.md"))
        if md_bestanden:
            try:
                inhoud = md_bestanden[0].read_text(encoding="utf-8")
                logger.info(
                    "Rapport geladen uit %s voor project %s",
                    md_bestanden[0],
                    project_id,
                )
                return {
                    "project_id": project_id,
                    "inhoud": inhoud,
                    "bestand": md_bestanden[0].name,
                }
            except OSError as exc:
                logger.error("Kon rapport niet lezen: %s", exc)

    # 2. Fallback op rapport_pad uit database
    if project.rapport_pad:
        rapport_path = Path(project.rapport_pad)
        if rapport_path.exists():
            try:
                inhoud = rapport_path.read_text(encoding="utf-8")
                return {
                    "project_id": project_id,
                    "inhoud": inhoud,
                    "bestand": rapport_path.name,
                }
            except OSError as exc:
                logger.error("Kon rapport niet lezen via rapport_pad: %s", exc)

    raise HTTPException(
        status_code=404,
        detail=f"Geen rapport beschikbaar voor project {project_id}",
    )


@router.get(
    "/projects/{project_id}/diagrams",
    summary="Diagrammen ophalen",
)
async def get_diagrams(
    project_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[dict]:
    """
    Haal de lijst van architectuurdiagrammen op voor een project.

    - Gebruikt DiagramRenderer indien beschikbaar
    - Fallback: leest JSON-bestanden uit `documentatie/diagrammen/{project_id}/`
    """
    result = await db.execute(
        select(ClientProject).where(ClientProject.project_id == project_id)
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} niet gevonden",
        )

    # Gebruik DiagramRenderer indien beschikbaar
    try:
        from ollama.diagram_renderer import get_diagram_renderer  # noqa: PLC0415

        renderer = get_diagram_renderer()
        diagrams = renderer.list_diagrams(project_id=project_id)
        logger.debug(
            "DiagramRenderer geeft %d diagrammen terug voor project %s",
            len(diagrams),
            project_id,
        )
        return [d.to_dict() for d in diagrams]
    except Exception as exc:
        logger.warning("DiagramRenderer niet beschikbaar: %s", exc)

    # Fallback: lees JSON-bestanden uit documentatie/diagrammen/{project_id}/
    diagrammen_dir = Path("documentatie") / "diagrammen" / project_id
    if not diagrammen_dir.exists():
        return []

    resultaten: list[dict] = []
    for json_bestand in sorted(diagrammen_dir.glob("*.json")):
        try:
            data = json.loads(json_bestand.read_text(encoding="utf-8"))
            resultaten.append(data)
        except Exception as exc:
            logger.warning("Fout bij laden diagram %s: %s", json_bestand, exc)

    return resultaten


@router.get(
    "/forecasts",
    response_model=KostenSchatting,
    summary="Kostenschatting berekenen",
)
async def bereken_kostenschatting(
    project_type: str = Query("code_analyse", description="Projecttype"),
    bestanden_aantal: int = Query(10, ge=1, description="Aantal te analyseren bestanden"),
    gem_bestandsgrootte_kb: int = Query(50, ge=1, description="Gemiddelde bestandsgrootte in KB"),
) -> KostenSchatting:
    """
    Bereken een schatting van kosten, tokens en analyse-duur.

    - Gebruikt CostForecaster indien beschikbaar
    - Fallback: hardgecodeerde schattingen per projecttype
    """
    # Hardgecodeerde fallback schattingen (lokale Ollama: kosten altijd €0,00)
    hardcoded: dict[str, KostenSchatting] = {
        "code_analyse": KostenSchatting(
            project_type="code_analyse",
            geschatte_tokens=bestanden_aantal * gem_bestandsgrootte_kb * 200,
            geschatte_kosten_eur=0.0,
            geschatte_minuten=max(5, bestanden_aantal * 3),
            betrouwbaarheid_percent=70,
        ),
        "bedrijfsproces": KostenSchatting(
            project_type="bedrijfsproces",
            geschatte_tokens=bestanden_aantal * gem_bestandsgrootte_kb * 150,
            geschatte_kosten_eur=0.0,
            geschatte_minuten=max(10, bestanden_aantal * 5),
            betrouwbaarheid_percent=65,
        ),
        "security_audit": KostenSchatting(
            project_type="security_audit",
            geschatte_tokens=bestanden_aantal * gem_bestandsgrootte_kb * 250,
            geschatte_kosten_eur=0.0,
            geschatte_minuten=max(15, bestanden_aantal * 7),
            betrouwbaarheid_percent=60,
        ),
    }

    fallback = hardcoded.get(
        project_type,
        KostenSchatting(
            project_type=project_type,
            geschatte_tokens=bestanden_aantal * gem_bestandsgrootte_kb * 200,
            geschatte_kosten_eur=0.0,
            geschatte_minuten=max(5, bestanden_aantal * 4),
            betrouwbaarheid_percent=50,
        ),
    )

    # Probeer CostForecaster
    try:
        from ollama.adaptive_chunker import ChunkConfig  # noqa: PLC0415
        from ollama.cost_forecaster import get_cost_forecaster  # noqa: PLC0415

        forecaster = get_cost_forecaster()
        schatting = forecaster.bereken_schatting(
            project_id="forecast-preview",
            bestanden=[],
            model="mistral",
            config=ChunkConfig(model="mistral"),
        )
        return KostenSchatting(
            project_type=project_type,
            geschatte_tokens=schatting.geschatte_tokens,
            geschatte_kosten_eur=schatting.geschatte_kosten_eur,
            geschatte_minuten=int(schatting.geschatte_duur_minuten),
            betrouwbaarheid_percent=80,
        )
    except Exception as exc:
        logger.debug(
            "CostForecaster niet beschikbaar, gebruik hardcoded schatting: %s", exc
        )

    return fallback
