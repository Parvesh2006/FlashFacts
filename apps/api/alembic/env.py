import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import Column, MetaData, PrimaryKeyConstraint, String, Table, inspect, text

from alembic import context
from alembic.ddl.impl import DefaultImpl

# Add app directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.database import Base
import app.models  # load all models for target_metadata

# Alembic defaults to String(32) for the alembic_version.version_num column.
# Several revision IDs in FlashFacts (e.g., '002_event_enrichment_and_entities' with 33 chars)
# exceed 32 characters, which causes a DataError on fresh PostgreSQL databases (such as Neon on Render).
# Overriding DefaultImpl.version_table_impl ensures that whenever alembic_version is created
# (both online and offline --sql), it uses VARCHAR(255).
def _custom_version_table_impl(
    self,
    *,
    version_table: str,
    version_table_schema: str | None,
    version_table_pk: bool,
    **kw,
) -> Table:
    vt = Table(
        version_table,
        MetaData(),
        Column("version_num", String(255), nullable=False),
        schema=version_table_schema,
    )
    if version_table_pk:
        vt.append_constraint(
            PrimaryKeyConstraint("version_num", name=f"{version_table}_pkc")
        )
    return vt

DefaultImpl.version_table_impl = _custom_version_table_impl


def _ensure_version_column_length(connection, version_table: str = "alembic_version") -> None:
    """
    Ensure the version_num column in alembic_version is at least VARCHAR(255).
    Safely widens the column if the table already exists with a shorter length (e.g. VARCHAR(32)).
    """
    try:
        inspector = inspect(connection)
        if inspector.has_table(version_table):
            columns = inspector.get_columns(version_table)
            for col in columns:
                if col["name"] == "version_num":
                    col_type = col.get("type")
                    col_length = getattr(col_type, "length", None)
                    if col_length is not None and col_length < 255:
                        dialect_name = connection.dialect.name
                        if dialect_name == "postgresql":
                            connection.execute(
                                text(f'ALTER TABLE "{version_table}" ALTER COLUMN "version_num" TYPE VARCHAR(255)')
                            )
                        elif dialect_name in ("mysql", "mariadb"):
                            connection.execute(
                                text(f'ALTER TABLE `{version_table}` MODIFY COLUMN `version_num` VARCHAR(255) NOT NULL')
                            )
                        break
    except Exception as exc:
        import logging
        logging.getLogger("alembic.env").warning("Could not verify/widen alembic_version column: %s", exc)

try:
    config = context.config
except AttributeError:
    config = None

if config and config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            _ensure_version_column_length(connection)
            context.run_migrations()

if config is not None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
