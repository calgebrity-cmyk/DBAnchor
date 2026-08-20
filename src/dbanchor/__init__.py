""" DBAnchor -- Safe Universal Database Developer-Experience Middleware & Diagnostics for PostgreSQL.

Core Promise:
    Put DATABASE_URL in .env. DBAnchor handles connection setup, validation,
    environment detection, migration state detection, health checks, deterministic diagnostics,
    and safe migration workflows with zero boilerplate.
"""

from dbanchor.config.loader import load_config
from dbanchor.config.models import ConnectionConfig, DBAnchorConfig, MigrationConfig, SafetyConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.connection.url import ConnectionInfo, parse_connection_url
from dbanchor.core.database import Database, DBAnchor
from dbanchor.diagnostics.engine import DiagnosticEngine, DiagnosticExplanation
from dbanchor.environments.detector import EnvironmentTier, detect_environment
from dbanchor.health.models import (
    CheckStatus,
    HealthCheckResult,
    HealthReport,
    OverallHealthStatus,
    Severity,
)
from dbanchor.health.runner import HealthRunner
from dbanchor.migrations.adopt import AdoptionPlan, AdoptionResult
from dbanchor.migrations.executor import MigrationExecutionResult
from dbanchor.migrations.planner import MigrationPlan
from dbanchor.migrations.state import MigrationRevision, MigrationState
from dbanchor.output.redaction import redact_secrets, redact_url
from dbanchor.providers.detector import detect_provider
from dbanchor.providers.models import ProviderMetadata, ProviderType
from dbanchor.safety.models import DestructiveOperation, OperationType, RiskLevel, SafetyAssessment
from dbanchor.schema.models import (
    ColumnSnapshot,
    DriftReport,
    DriftType,
    ForeignKeySnapshot,
    IndexSnapshot,
    SchemaDifference,
    SchemaSnapshot,
    TableSnapshot,
)

__version__ = "0.1.0"

__all__ = [
    "Database",
    "DBAnchor",
    "__version__",
    # Config
    "DBAnchorConfig",
    "ConnectionConfig",
    "MigrationConfig",
    "SafetyConfig",
    "load_config",
    # Connection
    "ConnectionInfo",
    "DatabaseConnector",
    "parse_connection_url",
    # Health
    "HealthReport",
    "HealthCheckResult",
    "CheckStatus",
    "OverallHealthStatus",
    "Severity",
    "HealthRunner",
    # Providers
    "ProviderMetadata",
    "ProviderType",
    "detect_provider",
    # Environment
    "EnvironmentTier",
    "detect_environment",
    # Migrations
    "MigrationState",
    "MigrationRevision",
    "MigrationPlan",
    "MigrationExecutionResult",
    "AdoptionPlan",
    "AdoptionResult",
    # Schema
    "SchemaSnapshot",
    "TableSnapshot",
    "ColumnSnapshot",
    "IndexSnapshot",
    "ForeignKeySnapshot",
    "DriftReport",
    "DriftType",
    "SchemaDifference",
    # Safety
    "RiskLevel",
    "OperationType",
    "DestructiveOperation",
    "SafetyAssessment",
    # Diagnostics
    "DiagnosticEngine",
    "DiagnosticExplanation",
    # Redaction
    "redact_url",
    "redact_secrets",
]
