"""
Lead model — contactformulier inzendingen van de freelance website.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    naam: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), index=True)
    bedrijf: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dienst: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bericht: Mapped[str] = mapped_column(Text)
    aangemaakt_op: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    verwerkt: Mapped[bool] = mapped_column(Boolean, default=False)
    notificatie_verzonden: Mapped[bool] = mapped_column(Boolean, default=False)
