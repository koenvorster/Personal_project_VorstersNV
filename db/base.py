"""SQLAlchemy declarative Base — losgekoppeld van de engine zodat Alembic het kan importeren."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
