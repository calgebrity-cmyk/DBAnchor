"""Integration tests for Alembic operations and state parsing."""

from pathlib import Path
from dbanchor.migrations.planner import plan_migrations
from dbanchor.migrations.state import inspect_migration_state


def test_inspect_migration_state_missing_ini(tmp_path: Path):
    state = inspect_migration_state(alembic_ini_path=tmp_path / "nonexistent.ini")
    assert state.is_alembic_configured is False


def test_plan_migrations_empty():
    plan = plan_migrations()
    assert plan.is_safe_to_apply is True
    assert plan.total_steps == 0
