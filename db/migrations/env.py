import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

# Voeg projectroot toe aan sys.path zodat imports werken
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from db.base import Base
from db.models.user import User  # noqa: F401 – zorgt dat User ook in migraties zit

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

DB_URL = os.environ.get(
    "DB_URL",
    "postgresql+psycopg2://vorstersNV:dev-password-change-me@localhost:5432/vorstersNV",
)
# Alembic vereist een synchrone driver — vervang asyncpg door psycopg2 indien nodig
DB_URL = DB_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
config.set_main_option("sqlalchemy.url", DB_URL)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode met een synchrone psycopg2 connectie."""
    from sqlalchemy import create_engine

    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),  # type: ignore[arg-type]
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
