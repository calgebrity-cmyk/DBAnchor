"""Safe migration executor for DBAnchor."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

from dbanchor.config.models import DBAnchorConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.diagnostics.engine import DiagnosticEngine, DiagnosticExplanation
from dbanchor.environments.detector import EnvironmentTier
from dbanchor.migrations.planner import MigrationPlan, plan_migrations
from dbanchor.migrations.state import find_alembic_config_path, inspect_migration_state
from dbanchor.safety.guard import SafetyGuard, SafetyGuardError


class MigrationExecutionResult(BaseModel):
    """Result of migration execution."""
    success: bool
    applied_count: int = 0
    from_revision: Optional[str] = None
    to_revision: Optional[str] = None
    elapsed_ms: float = 0.0
    message: str = ""
    diagnostic: Optional[DiagnosticExplanation] = None


def execute_migrations(
    config: DBAnchorConfig,
    connector: DatabaseConnector,
    target_revision: str = "head",
    dry_run: bool = False,
    force_destructive: bool = False,
    alembic_ini_path: Optional[str | Path] = None,
) -> MigrationExecutionResult:
    """Safely apply pending migrations to the database with safety checks."""
    start_time = time.perf_counter()

    # 1. Generate plan & safety review
    plan = plan_migrations(
        connector=connector,
        alembic_ini_path=alembic_ini_path,
    )

    if not plan.pending_revisions:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return MigrationExecutionResult(
            success=True,
            applied_count=0,
            from_revision=plan.source_revision,
            to_revision=plan.target_revision,
            elapsed_ms=elapsed,
            message="Database is already up to date. No migrations to apply.",
        )

    # 2. Dry run preview only
    if dry_run:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return MigrationExecutionResult(
            success=True,
            applied_count=len(plan.pending_revisions),
            from_revision=plan.source_revision,
            to_revision=plan.target_revision,
            elapsed_ms=elapsed,
            message=f"Dry run complete. {len(plan.pending_revisions)} pending migration(s) planned.",
        )

    # 3. Enforce Safety Guard
    try:
        SafetyGuard.enforce(
            assessment=plan.safety_assessment,
            environment=config.environment,
            force_destructive=force_destructive or config.safety.allow_destructive,
        )
    except SafetyGuardError as sge:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        diag = DiagnosticEngine.diagnose_error(str(sge))
        return MigrationExecutionResult(
            success=False,
            from_revision=plan.source_revision,
            to_revision=plan.target_revision,
            elapsed_ms=elapsed,
            message=str(sge),
            diagnostic=diag,
        )

    # 4. Execute Alembic Upgrade
    try:
        from alembic import command
        from alembic.config import Config

        ini_path = Path(alembic_ini_path) if alembic_ini_path else find_alembic_config_path()
        if not ini_path:
            raise FileNotFoundError("alembic.ini not found")

        alembic_cfg = Config(str(ini_path))
        # Override SQLAlchemy URL dynamically
        if config.connection.url:
            alembic_cfg.set_main_option("sqlalchemy.url", connector.connection_info.normalized_url)

        command.upgrade(alembic_cfg, target_revision)

        # Inspect updated state
        new_state = inspect_migration_state(connector=connector, alembic_ini_path=ini_path)
        elapsed = (time.perf_counter() - start_time) * 1000.0

        return MigrationExecutionResult(
            success=True,
            applied_count=len(plan.pending_revisions),
            from_revision=plan.source_revision,
            to_revision=new_state.current_db_revision,
            elapsed_ms=elapsed,
            message=f"Successfully applied {len(plan.pending_revisions)} migration(s). Database is at revision '{new_state.current_db_revision}'.",
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        diag = DiagnosticEngine.diagnose_error(e, {"operation": "alembic upgrade"})
        return MigrationExecutionResult(
            success=False,
            from_revision=plan.source_revision,
            to_revision=plan.target_revision,
            elapsed_ms=elapsed,
            message=f"Migration execution failed: {e}",
            diagnostic=diag,
        )
