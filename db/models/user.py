"""
VorstersNV User & Rollen model
Rollen: admin, klant, tester
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, PyEnum):
    admin = "admin"
    klant = "klant"
    tester = "tester"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    wachtwoord_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.klant, nullable=False)
    actief: Mapped[bool] = mapped_column(Boolean, default=True)
    aangemaakt_op: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    laatste_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
