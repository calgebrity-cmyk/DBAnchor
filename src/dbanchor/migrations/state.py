"""Alembic migration state and revision graph inspector."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Engine, text

from dbanchor.connection.connector import DatabaseConnector


class MigrationRevision(BaseModel):
    """Metadata for an individual Alembic migration script."""
    revision: str
    down_revision: Optional[str] = None
    message: Optional[str] = None
    path: Optional[str] = None


class MigrationState(BaseModel):
    """Live state of Alembic migration history and database revisions."""
    is_alembic_configured: bool = False
    config_path: Optional[str] = None
    script_dir: Optional[str] = None
    database_revisions: list[str] = Field(default_factory=list)
    codebase_heads: list[str] = Field(default_factory=list)
    pending_revisions: list[MigrationRevision] = Field(default_factory=list)
    is_up_to_date: bool = False
    has_multiple_heads: bool = False
    is_diverged: bool = False
    is_fresh_db: bool = False
    status_summary: str = ""

    @property
    def current_db_revision(self) -> Optional[str]:
        return self.database_revisions[0] if self.database_revisions else None

    @property
    def head_revision(self) -> Optional[str]:
        return self.codebase_heads[0] if self.codebase_heads else None

    @property
    def pending_count(self) -> int:
        return len(self.pending_revisions)


def find_alembic_config_path(start_path: Path | None = None) -> Optional[Path]:
    """Find alembic.ini in directory or parents."""
    curr = (start_path or Path.cwd()).resolve()
    for directory in [curr, *curr.parents]:
        ini = directory / "alembic.ini"
        if ini.is_file():
            return ini
    return None


def inspect_migration_state(
    connector: Optional[DatabaseConnector] = None,
    engine: Optional[Engine] = None,
    alembic_ini_path: Optional[str | Path] = None,
) -> MigrationState:
    """Inspect local Alembic script revisions and live database revision table."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
    except ImportError:
        return MigrationState(
            is_alembic_configured=False,
            status_summary="Alembic is not installed in the environment.",
        )

    # 1. Locate alembic.ini
    ini_path = Path(alembic_ini_path) if alembic_ini_path else find_alembic_config_path()
    if not ini_path or not ini_path.is_file():
        return MigrationState(
            is_alembic_configured=False,
            status_summary="No alembic.ini found in project root or parent directories.",
        )

    alembic_cfg = Config(str(ini_path))
    try:
        script = ScriptDirectory.from_config(alembic_cfg)
    except Exception as e:
        return MigrationState(
            is_alembic_configured=True,
            config_path=str(ini_path),
            status_summary=f"Failed to load Alembic scripts directory: {e}",
        )

    # 2. Get codebase heads
    heads = list(script.get_heads())
    has_multiple_heads = len(heads) > 1

    # 3. Read live database revision from alembic_version table
    target_engine = engine or (connector.get_sync_engine() if connector else None)
    db_revisions: list[str] = []
    is_fresh = True

    if target_engine:
        try:
            with target_engine.connect() as conn:
                res = conn.execute(text("SELECT version_num FROM alembic_version;")).fetchall()
                if res:
                    db_revisions = [row[0] for row in res]
                    is_fresh = False
        except Exception:
            # Table doesn't exist yet -> fresh database
            is_fresh = True

    # 4. Calculate pending revisions
    pending: list[MigrationRevision] = []
    is_up_to_date = False
    is_diverged = False

    if not db_revisions:
        # All revisions from base to head are pending
        try:
            for rev in script.walk_revisions("base", "heads"):
                down_rev = (
                    rev.down_revision
                    if isinstance(rev.down_revision, str)
                    else ", ".join(rev.down_revision) if rev.down_revision
                    else None
                )
                pending.insert(
                    0,
                    MigrationRevision(
                        revision=rev.revision,
                        down_revision=down_rev,
                        message=rev.doc,
                        path=rev.path,
                    ),
                )
        except Exception:
            pass
        status_summary = f"Database is unmigrated. {len(pending)} pending migrations."
    else:
        current_rev = db_revisions[0]
        if heads and current_rev in heads and not has_multiple_heads:
            is_up_to_date = True
            status_summary = f"Database is UP TO DATE at revision {current_rev}."
        else:
            try:
                # Walk from current DB revision to heads
                rev_list = list(script.walk_revisions(current_rev, "heads"))
                for rev in rev_list:
                    if rev.revision != current_rev:
                        down_rev = (
                            rev.down_revision
                            if isinstance(rev.down_revision, str)
                            else ", ".join(rev.down_revision) if rev.down_revision
                            else None
                        )
                        pending.insert(
                            0,
                            MigrationRevision(
                                revision=rev.revision,
                                down_revision=down_rev,
                                message=rev.doc,
                                path=rev.path,
                            ),
                        )
                status_summary = f"Database is OUT OF DATE. {len(pending)} pending migrations."
            except Exception:
                # Revision not found in script history -> diverged!
                is_diverged = True
                status_summary = (
                    f"Migration history DIVERGED. DB revision '{current_rev}' is not in codebase."
                )

    return MigrationState(
        is_alembic_configured=True,
        config_path=str(ini_path),
        script_dir=str(script.dir),
        database_revisions=db_revisions,
        codebase_heads=heads,
        pending_revisions=pending,
        is_up_to_date=is_up_to_date,
        has_multiple_heads=has_multiple_heads,
        is_diverged=is_diverged,
        is_fresh_db=is_fresh,
        status_summary=status_summary,
    )
