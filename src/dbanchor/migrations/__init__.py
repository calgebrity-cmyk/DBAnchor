"""Migration management, planning, and execution for DBAnchor."""

from dbanchor.migrations.adopt import AdoptionPlan, AdoptionResult, adopt_project, plan_adoption
from dbanchor.migrations.executor import MigrationExecutionResult, execute_migrations
from dbanchor.migrations.planner import MigrationPlan, plan_migrations
from dbanchor.migrations.state import (
    MigrationRevision,
    MigrationState,
    find_alembic_config_path,
    inspect_migration_state,
)

__all__ = [
    "MigrationState",
    "MigrationRevision",
    "MigrationPlan",
    "MigrationExecutionResult",
    "AdoptionPlan",
    "AdoptionResult",
    "inspect_migration_state",
    "plan_migrations",
    "execute_migrations",
    "plan_adoption",
    "adopt_project",
    "find_alembic_config_path",
]
