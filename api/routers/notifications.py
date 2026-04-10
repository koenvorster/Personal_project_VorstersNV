"""
VorstersNV Notifications API Router
E-mail en push notificaties via de email_template_agent.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models.models import AgentLog

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class EmailNotificatieIn(BaseModel):
    email_type: str = Field(
        ...,
        description="Type e-mail: order_bevestiging, verzend_bevestiging, retour_bevestiging, low_stock_alert",
        examples=["order_bevestiging"],
    )
    ontvanger_email: str = Field(..., examples=["klant@voorbeeld.nl"])
    ontvanger_naam: str = Field(..., examples=["Jan Janssen"])
    context: dict = Field(default_factory=dict, description="Extra context voor de email template agent")


class NotificatieResponse(BaseModel):
    id: int
    email_type: str
    ontvanger_email: str
    ontvanger_naam: str
    agent_output: str
    verstuurd_op: str


class NotificatieListResponse(BaseModel):
    items: list[NotificatieResponse]
    totaal: int
    pagina: int
    per_pagina: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/email",
    response_model=NotificatieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="E-mail notificatie versturen",
    description="Genereert een e-mail via de email_template_agent en logt deze in de database.",
)
async def stuur_email_notificatie(
    notificatie: EmailNotificatieIn,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Stuur een e-mail notificatie via de email_template_agent.

    Beschikbare email_types:
    - **order_bevestiging**: Bevestiging na plaatsen order
    - **verzend_bevestiging**: Bevestiging bij verzending met tracking
    - **retour_bevestiging**: Bevestiging bij retour ontvangst
    - **low_stock_alert**: Interne alert voor lage voorraad (admin)
    """
    user_input = (
        f"email_type: {notificatie.email_type}\n"
        f"ontvanger: {notificatie.ontvanger_naam} <{notificatie.ontvanger_email}>\n"
        f"context: {notificatie.context}"
    )

    # Probeer de email_template_agent te gebruiken indien beschikbaar
    agent_output = _genereer_email_tekst(notificatie)

    log_entry = AgentLog(
        agent_naam="email_template_agent",
        model="mistral",
        user_input=user_input,
        agent_output=agent_output,
        prompt_versie="1.0",
    )
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)

    logger.info(
        "E-mail notificatie verstuurd: type=%s, ontvanger=%s",
        notificatie.email_type,
        notificatie.ontvanger_email,
    )

    return NotificatieResponse(
        id=log_entry.id,
        email_type=notificatie.email_type,
        ontvanger_email=notificatie.ontvanger_email,
        ontvanger_naam=notificatie.ontvanger_naam,
        agent_output=agent_output,
        verstuurd_op=log_entry.aangemaakt_op.isoformat(),
    )


@router.get(
    "/",
    response_model=NotificatieListResponse,
    summary="Recente notificaties",
    description="Haal een overzicht op van alle verstuurde e-mail notificaties.",
)
async def lijst_notificaties(
    db: Annotated[AsyncSession, Depends(get_db)],
    pagina: int = Query(1, ge=1),
    per_pagina: int = Query(20, ge=1, le=100),
    email_type: str | None = Query(None, description="Filter op email type"),
):
    """Overzicht van alle notificaties via de email_template_agent."""
    q = select(AgentLog).where(AgentLog.agent_naam == "email_template_agent")
    if email_type:
        q = q.where(AgentLog.user_input.contains(f"email_type: {email_type}"))

    from sqlalchemy import func

    count_q = select(func.count(AgentLog.id)).where(AgentLog.agent_naam == "email_template_agent")
    if email_type:
        count_q = count_q.where(AgentLog.user_input.contains(f"email_type: {email_type}"))

    total_result = await db.execute(count_q)
    total = total_result.scalar_one_or_none() or 0

    q = q.order_by(AgentLog.aangemaakt_op.desc()).offset((pagina - 1) * per_pagina).limit(per_pagina)
    result = await db.execute(q)
    logs = result.scalars().all()

    items = []
    for log in logs:
        ontvanger_email, ontvanger_naam, email_type_val = _parse_log_input(log.user_input)
        items.append(NotificatieResponse(
            id=log.id,
            email_type=email_type_val,
            ontvanger_email=ontvanger_email,
            ontvanger_naam=ontvanger_naam,
            agent_output=log.agent_output,
            verstuurd_op=log.aangemaakt_op.isoformat(),
        ))

    return NotificatieListResponse(items=items, totaal=total, pagina=pagina, per_pagina=per_pagina)


@router.get(
    "/{notificatie_id}",
    response_model=NotificatieResponse,
    summary="Notificatie detail",
    responses={404: {"description": "Notificatie niet gevonden"}},
)
async def get_notificatie(
    notificatie_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Haal een specifieke notificatie op via ID."""
    result = await db.execute(
        select(AgentLog).where(
            AgentLog.id == notificatie_id,
            AgentLog.agent_naam == "email_template_agent",
        )
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail=f"Notificatie {notificatie_id} niet gevonden")

    ontvanger_email, ontvanger_naam, email_type_val = _parse_log_input(log.user_input)
    return NotificatieResponse(
        id=log.id,
        email_type=email_type_val,
        ontvanger_email=ontvanger_email,
        ontvanger_naam=ontvanger_naam,
        agent_output=log.agent_output,
        verstuurd_op=log.aangemaakt_op.isoformat(),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _genereer_email_tekst(notificatie: EmailNotificatieIn) -> str:
    """Genereer basis e-mail tekst op basis van type. In productie: vervang door email_template_agent aanroep."""
    templates = {
        "order_bevestiging": (
            f"Beste {notificatie.ontvanger_naam},\n\n"
            "Bedankt voor uw bestelling bij VorstersNV! Wij hebben uw order ontvangen "
            "en zullen deze zo spoedig mogelijk verwerken.\n\n"
            f"Ordergegevens: {notificatie.context}\n\n"
            "Met vriendelijke groet,\nHet VorstersNV Team"
        ),
        "verzend_bevestiging": (
            f"Beste {notificatie.ontvanger_naam},\n\n"
            "Geweldig nieuws! Uw bestelling is onderweg.\n\n"
            f"Trackinggegevens: {notificatie.context.get('tracking_code', 'n.v.t.')}\n\n"
            "Met vriendelijke groet,\nHet VorstersNV Team"
        ),
        "retour_bevestiging": (
            f"Beste {notificatie.ontvanger_naam},\n\n"
            "Wij hebben uw retour ontvangen en in goede orde verwerkt.\n\n"
            "De terugbetaling wordt binnen 5 werkdagen verwerkt.\n\n"
            "Met vriendelijke groet,\nHet VorstersNV Team"
        ),
        "low_stock_alert": (
            f"[INTERN - LOW STOCK ALERT]\n\n"
            f"Product: {notificatie.context.get('product_naam', 'onbekend')}\n"
            f"Huidige voorraad: {notificatie.context.get('voorraad', '?')}\n"
            f"Drempel: {notificatie.context.get('drempel', '?')}\n\n"
            "Actie vereist: voorraad bijbestellen."
        ),
    }
    return templates.get(
        notificatie.email_type,
        f"Notificatie voor {notificatie.ontvanger_naam}: {notificatie.context}",
    )


def _parse_log_input(user_input: str) -> tuple[str, str, str]:
    """Parse gestruct e-mail log input terug naar velden."""
    email_type, ontvanger_email, ontvanger_naam = "onbekend", "onbekend", "onbekend"
    for line in user_input.splitlines():
        if line.startswith("email_type: "):
            email_type = line.removeprefix("email_type: ").strip()
        elif line.startswith("ontvanger: "):
            part = line.removeprefix("ontvanger: ").strip()
            if "<" in part and ">" in part:
                ontvanger_naam = part.split("<")[0].strip()
                ontvanger_email = part.split("<")[1].rstrip(">").strip()
    return ontvanger_email, ontvanger_naam, email_type
