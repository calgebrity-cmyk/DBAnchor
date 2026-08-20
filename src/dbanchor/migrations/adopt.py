"""Adoption engine for unmanaged or legacy databases into DBAnchor workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import text

from dbanchor.connection.connector import DatabaseConnector
from dbanchor.migrations.state import MigrationState, inspect_migration_state
from dbanchor.schema.inspector import SchemaInspector
from dbanchor.schema.models import SchemaSnapshot

ALEMBIC_INI_TEMPLATE = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
# file_template = %%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
# defaults to the current working directory.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
# timezone =

# max length of characters to apply to the
# "slug" field
# truncate_slug_length = 40

# set to 'true' to run the environment during
# the 'revision' command, regardless of autogenerate
# revision_environment = false

# set to 'true' to allow .pyc and .pyo files without
# a source .py file to be detected as revisions in the
# versions/ directory
# sourceless = false

# version location specification; This defaults
# to migrations/versions. When using multiple version
# directories, initial revisions must be specified with --version-path.
# The path separator used here should be the separator specified by "version_path_separator" below.
# version_locations = %(here)s/bar:%(here)s/bat:migrations/versions

# version path separator; as mentioned above, this is the character used to
# split version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
# version_path_separator = :
# version_path_separator = ;
# version_path_separator = space
version_path_separator = os

# the output encoding used when revision files
# are written from script.py.mako
# output_encoding = utf-8

sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/app_db


[post_write_hooks]
# logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

ENV_PY_TEMPLATE = """import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with DATABASE_URL environment variable if set
db_url = os.getenv("DATABASE_URL")
if db_url:
    # Normalize postgres:// to postgresql://
    if db_url.startswith("postgres://"):
        db_url = "postgresql://" + db_url[len("postgres://"):]
    config.set_main_option("sqlalchemy.url", db_url)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import models
# target_metadata = models.Base.metadata
target_metadata = None

def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
"""

SCRIPT_PY_MAKO_TEMPLATE = """\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
"""


class AdoptionPlan(BaseModel):
    """Adoption recommendations for an existing project."""
    table_count: int = 0
    tables: list[str] = Field(default_factory=list)
    has_alembic_setup: bool = False
    needs_baseline: bool = True
    steps: list[str] = Field(default_factory=list)


class AdoptionResult(BaseModel):
    """Result of running dbx adopt."""
    success: bool
    tables_preserved: int = 0
    baseline_revision: Optional[str] = None
    message: str = ""


def plan_adoption(
    connector: DatabaseConnector,
    project_root: str | Path | None = None,
) -> AdoptionPlan:
    """Analyze existing database and project files to formulate a non-destructive adoption plan."""
    root = Path(project_root or Path.cwd()).resolve()

    # 1. Inspect live database tables
    inspector = SchemaInspector(connector)
    snapshot = inspector.inspect_schema()
    table_names = [t for t in snapshot.tables.keys() if t != "alembic_version"]

    # 2. Inspect migration state
    state = inspect_migration_state(connector=connector)

    steps: list[str] = []
    steps.append("1. Preserve all existing live tables and data (Zero data deletion).")

    if not state.is_alembic_configured:
        steps.append("2. Initialize Alembic configuration structure (alembic.ini, migrations/env.py).")
        steps.append("3. Create initial baseline migration corresponding to current live schema.")
        steps.append("4. Stamp alembic_version table to the baseline revision.")
    else:
        steps.append("2. Inspect schema diff between current models and live database.")
        steps.append("3. Align local head revisions with live database state.")

    steps.append("5. Verify database connection and ready status with 'dbx doctor'.")

    return AdoptionPlan(
        table_count=len(table_names),
        tables=table_names,
        has_alembic_setup=state.is_alembic_configured,
        needs_baseline=not state.is_up_to_date,
        steps=steps,
    )


def adopt_project(
    connector: DatabaseConnector,
    project_root: str | Path | None = None,
) -> AdoptionResult:
    """Execute non-destructive adoption of existing database."""
    root = Path(project_root or Path.cwd()).resolve()
    plan = plan_adoption(connector, root)

    try:
        # 1. Create alembic.ini if missing
        ini_file = root / "alembic.ini"
        if not ini_file.is_file():
            ini_file.write_text(ALEMBIC_INI_TEMPLATE, encoding="utf-8")

        # 2. Create migrations directory if missing
        mig_dir = root / "migrations"
        mig_dir.mkdir(exist_ok=True)
        (mig_dir / "versions").mkdir(exist_ok=True)

        env_file = mig_dir / "env.py"
        if not env_file.is_file():
            env_file.write_text(ENV_PY_TEMPLATE, encoding="utf-8")

        mako_file = mig_dir / "script.py.mako"
        if not mako_file.is_file():
            mako_file.write_text(SCRIPT_PY_MAKO_TEMPLATE, encoding="utf-8")

        # 3. Create baseline revision file
        baseline_rev = "0001_baseline"
        baseline_path = mig_dir / "versions" / f"{baseline_rev}_initial.py"
        if not baseline_path.is_file():
            baseline_code = f'''"""initial baseline

Revision ID: {baseline_rev}
Revises: 
Create Date: 2026-08-20 00:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '{baseline_rev}'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Baseline adoption: existing tables are preserved
    pass

def downgrade() -> None:
    pass
'''
            baseline_path.write_text(baseline_code, encoding="utf-8")

        # 4. Stamp database alembic_version table to baseline_rev
        engine = connector.get_sync_engine()
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"
                )
            )
            # Check if version exists
            res = conn.execute(text("SELECT version_num FROM alembic_version;")).fetchall()
            if not res:
                conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{baseline_rev}');"))
                conn.commit()

        return AdoptionResult(
            success=True,
            tables_preserved=plan.table_count,
            baseline_revision=baseline_rev,
            message=f"Project successfully adopted. Preserved {plan.table_count} existing tables and stamped baseline revision '{baseline_rev}'.",
        )
    except Exception as e:
        return AdoptionResult(
            success=False,
            tables_preserved=plan.table_count,
            message=f"Adoption failed: {e}",
        )
