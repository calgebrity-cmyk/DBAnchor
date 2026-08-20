"""Migration planning and dry-run safety assessment for DBAnchor."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Engine

from dbanchor.connection.connector import DatabaseConnector
from dbanchor.migrations.state import (
    MigrationRevision,
    MigrationState,
    inspect_migration_state,
)
from dbanchor.safety.analyzer import analyze_sql_safety
from dbanchor.safety.models import RiskLevel, SafetyAssessment


class MigrationPlan(BaseModel):
    """Dry-run migration plan with safety analysis."""
    source_revision: Optional[str] = None
    target_revision: Optional[str] = None
    pending_revisions: list[MigrationRevision] = Field(default_factory=list)
    safety_assessment: SafetyAssessment = Field(default_factory=SafetyAssessment)
    sql_preview: Optional[str] = None
    is_safe_to_apply: bool = True

    @property
    def total_steps(self) -> int:
        return len(self.pending_revisions)


def plan_migrations(
    connector: Optional[DatabaseConnector] = None,
    engine: Optional[Engine] = None,
    alembic_ini_path: Optional[str | Path] = None,
) -> MigrationPlan:
    """Generate a dry-run migration plan and evaluate safety risks."""
    state = inspect_migration_state(
        connector=connector,
        engine=engine,
        alembic_ini_path=alembic_ini_path,
    )

    if not state.is_alembic_configured or not state.pending_revisions:
        return MigrationPlan(
            source_revision=state.current_db_revision,
            target_revision=state.head_revision,
            pending_revisions=[],
            safety_assessment=SafetyAssessment(overall_risk=RiskLevel.LOW, is_destructive=False),
            is_safe_to_apply=True,
        )

    # Read migration files content to inspect operations and SQL
    raw_migration_code: list[str] = []
    for rev in state.pending_revisions:
        if rev.path and Path(rev.path).is_file():
            try:
                raw_migration_code.append(Path(rev.path).read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass

    combined_code = "\n".join(raw_migration_code)
    safety = analyze_sql_safety(combined_code)

    return MigrationPlan(
        source_revision=state.current_db_revision or "base",
        target_revision=state.head_revision,
        pending_revisions=state.pending_revisions,
        safety_assessment=safety,
        sql_preview=combined_code if len(combined_code) < 5000 else combined_code[:5000] + "\n... (truncated)",
        is_safe_to_apply=not safety.is_destructive,
    )
