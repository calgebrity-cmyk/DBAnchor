"""Core Database middleware class for DBAnchor."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Generator, Optional
from sqlalchemy import Engine, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import Session

from dbanchor.config.loader import load_config
from dbanchor.config.models import DBAnchorConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.connection.url import ConnectionInfo, parse_connection_url
from dbanchor.diagnostics.engine import DiagnosticEngine, DiagnosticExplanation
from dbanchor.environments.detector import EnvironmentTier
from dbanchor.health.models import HealthReport
from dbanchor.health.runner import HealthRunner
from dbanchor.migrations.adopt import AdoptionResult, adopt_project
from dbanchor.migrations.executor import MigrationExecutionResult, execute_migrations
from dbanchor.migrations.planner import MigrationPlan, plan_migrations
from dbanchor.migrations.state import MigrationState, inspect_migration_state
from dbanchor.providers.detector import detect_provider
from dbanchor.providers.models import ProviderMetadata
from dbanchor.schema.diff import compare_schemas
from dbanchor.schema.inspector import SchemaInspector
from dbanchor.schema.models import DriftReport, SchemaSnapshot


class Database:
    """Universal safe developer-experience database middleware for PostgreSQL."""

    def __init__(
        self,
        url: Optional[str] = None,
        env_file: Optional[str | Path] = None,
        config: Optional[DBAnchorConfig] = None,
        **kwargs: Any,
    ) -> None:
        if config is not None:
            self.config = config
        else:
            self.config = load_config(env_file=env_file, url_override=url)

        # Apply any ad-hoc overrides
        if url:
            self.config.connection.url = url
        for k, v in kwargs.items():
            if hasattr(self.config.connection, k):
                setattr(self.config.connection, k, v)

        if self.config.connection.url:
            self.conn_info: Optional[ConnectionInfo] = parse_connection_url(self.config.connection.url)
            self.connector: Optional[DatabaseConnector] = DatabaseConnector(
                self.config.connection, self.conn_info
            )
        else:
            self.conn_info = None
            self.connector = None

    @property
    def url(self) -> Optional[str]:
        return self.config.connection.url

    @property
    def safe_url(self) -> str:
        return self.conn_info.safe_url if self.conn_info else ""

    @property
    def environment(self) -> EnvironmentTier:
        return self.config.environment

    @property
    def engine(self) -> Engine:
        """Get cached sync SQLAlchemy Engine."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        return self.connector.get_sync_engine()

    @property
    def async_engine(self) -> AsyncEngine:
        """Get cached async SQLAlchemy AsyncEngine."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        return self.connector.get_async_engine()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context manager yielding a sync SQLAlchemy Session."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        session = self.connector.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async context manager yielding an async SQLAlchemy AsyncSession."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        session = self.connector.get_async_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def check_health(self) -> HealthReport:
        """Execute full non-destructive database health checks."""
        runner = HealthRunner(
            config=self.config,
            conn_info=self.conn_info,
            connector=self.connector,
        )
        return runner.run_health_checks()

    def get_provider(self) -> ProviderMetadata:
        """Detect database hosting provider."""
        return detect_provider(self.conn_info)

    def get_migration_status(self, alembic_ini_path: Optional[str | Path] = None) -> MigrationState:
        """Inspect current database and codebase migration state."""
        return inspect_migration_state(
            connector=self.connector,
            alembic_ini_path=alembic_ini_path or self.config.migrations.alembic_ini,
        )

    def plan_migrations(self, alembic_ini_path: Optional[str | Path] = None) -> MigrationPlan:
        """Generate a dry-run migration plan with safety analysis."""
        return plan_migrations(
            connector=self.connector,
            alembic_ini_path=alembic_ini_path or self.config.migrations.alembic_ini,
        )

    def migrate(
        self,
        target_revision: str = "head",
        dry_run: bool = False,
        force_destructive: bool = False,
        alembic_ini_path: Optional[str | Path] = None,
    ) -> MigrationExecutionResult:
        """Safely execute pending migrations with safety guardrails."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        return execute_migrations(
            config=self.config,
            connector=self.connector,
            target_revision=target_revision,
            dry_run=dry_run,
            force_destructive=force_destructive,
            alembic_ini_path=alembic_ini_path or self.config.migrations.alembic_ini,
        )

    def inspect_schema(self, schema_name: str = "public") -> SchemaSnapshot:
        """Reflect live database tables, columns, indexes, and foreign keys."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        inspector = SchemaInspector(self.connector)
        return inspector.inspect_schema(schema_name=schema_name)

    def diff_schema(
        self,
        expected_metadata: MetaData | SchemaSnapshot,
        schema_name: str = "public",
    ) -> DriftReport:
        """Compare expected application schema against actual live database schema."""
        actual_snap = self.inspect_schema(schema_name=schema_name)
        return compare_schemas(expected_metadata, actual_snap)

    def diagnose(self, exc: Exception | str, context: Optional[dict[str, Any]] = None) -> DiagnosticExplanation:
        """Get deterministic explanation, risk analysis, and safe fixes for an error."""
        ctx = context or {}
        if self.conn_info:
            ctx.setdefault("host", self.conn_info.host)
            ctx.setdefault("has_encoding_warning", self.conn_info.has_encoding_warning)
        return DiagnosticEngine.diagnose_error(exc, ctx)

    def adopt(self, project_root: str | Path | None = None) -> AdoptionResult:
        """Adopt an existing unmanaged database without data loss."""
        if not self.connector:
            raise ValueError("DATABASE_URL is not configured.")
        return adopt_project(self.connector, project_root)

    def close(self) -> None:
        """Dispose of underlying connection pools."""
        if self.connector:
            self.connector.close()


# Alias DBAnchor to Database
DBAnchor = Database
