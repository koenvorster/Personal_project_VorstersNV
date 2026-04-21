"""
Leads API Router — contactformulier inzendingen en offerte-aanvragen.
"""
import logging
import os

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Lead

logger = logging.getLogger(__name__)

router = APIRouter()

NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

DIENST_LABELS: dict[str, str] = {
    "full-stack": "Full-Stack Development",
    "ai-ml": "AI / Machine Learning",
    "iot": "IoT & Embedded",
    "consulting": "IT Consulting",
    "legacy-analyse": "Legacy Code Analyse",
    "intake": "Project Intake",
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class LeadRequest(BaseModel):
    naam: str
    email: EmailStr
    bedrijf: str | None = None
    dienst: str | None = None
    bericht: str

    @field_validator("naam")
    @classmethod
    def naam_niet_leeg(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Naam mag niet leeg zijn")
        return v.strip()

    @field_validator("bericht")
    @classmethod
    def bericht_niet_leeg(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Bericht moet minstens 10 tekens bevatten")
        return v.strip()


class LeadResponse(BaseModel):
    id: int
    boodschap: str = "Uw bericht is ontvangen. We nemen zo snel mogelijk contact op."

    model_config = {"from_attributes": True}


# ── Background tasks ──────────────────────────────────────────────────────────

async def _stuur_notificatie(lead_id: int, naam: str, email: str, dienst: str | None, db: AsyncSession) -> None:
    """Stuur een e-mailnotificatie bij een nieuwe lead (fire-and-forget)."""
    if not all([NOTIFY_EMAIL, SMTP_HOST, SMTP_USER, SMTP_PASSWORD]):
        logger.info("SMTP niet geconfigureerd — lead %d niet gemaild", lead_id)
        return
    try:
        import smtplib
        from email.mime.text import MIMEText

        dienst_label = DIENST_LABELS.get(dienst or "", dienst or "Niet opgegeven")
        body = (
            f"Nieuwe lead #{lead_id} ontvangen via VorstersNV.be\n\n"
            f"Naam:    {naam}\n"
            f"E-mail:  {email}\n"
            f"Dienst:  {dienst_label}\n\n"
            f"Bekijk details in het dashboard: https://vorstersNV.be/dashboard"
        )
        msg = MIMEText(body)
        msg["Subject"] = f"[VorstersNV] Nieuwe lead: {naam}"
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)

        # Markeer notificatie als verzonden
        from sqlalchemy import update
        await db.execute(
            update(Lead).where(Lead.id == lead_id).values(notificatie_verzonden=True)
        )
        await db.commit()
        logger.info("Notificatie verzonden voor lead %d", lead_id)
    except Exception:
        logger.exception("Notificatie mislukt voor lead %d", lead_id)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/leads",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Nieuw contactbericht / offerte-aanvraag",
    description="Slaat een lead op vanuit het contactformulier en stuurt een notificatie.",
)
async def create_lead(
    payload: LeadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    lead = Lead(
        naam=payload.naam,
        email=str(payload.email),
        bedrijf=payload.bedrijf,
        dienst=payload.dienst,
        bericht=payload.bericht,
    )
    db.add(lead)
    try:
        await db.commit()
        await db.refresh(lead)
    except Exception:
        await db.rollback()
        logger.exception("Lead opslaan mislukt")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bericht kon niet worden opgeslagen. Probeer opnieuw.",
        )

    background_tasks.add_task(_stuur_notificatie, lead.id, lead.naam, lead.email, lead.dienst, db)
    logger.info("Lead %d aangemaakt: %s <%s>", lead.id, lead.naam, lead.email)
    return LeadResponse(id=lead.id)
