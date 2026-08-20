"""Health check data models and status structures for DBAnchor."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from dbanchor.diagnostics.engine import DiagnosticExplanation
from dbanchor.environments.detector import EnvironmentTier
from dbanchor.providers.models import ProviderMetadata


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNKNOWN = "UNKNOWN"

    @property
    def icon(self) -> str:
        if self == CheckStatus.PASS:
            return "[+]"
        if self == CheckStatus.WARN:
            return "[!]"
        if self == CheckStatus.FAIL:
            return "[x]"
        if self == CheckStatus.SKIP:
            return "[-]"
        return "[?]"

    @property
    def color(self) -> str:
        if self == CheckStatus.PASS:
            return "green"
        if self == CheckStatus.WARN:
            return "yellow"
        if self == CheckStatus.FAIL:
            return "red"
        if self == CheckStatus.SKIP:
            return "dim"
        return "white"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HealthCheckResult(BaseModel):
    """Result of an individual subsystem health check."""
    name: str = Field(description="Name of the check (e.g. 'DNS', 'TCP', 'Authentication')")
    status: CheckStatus = Field(description="Execution status")
    severity: Severity = Field(default=Severity.INFO, description="Failure severity")
    message: str = Field(description="Human-readable result summary")
    elapsed_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    diagnostic: Optional[DiagnosticExplanation] = Field(
        default=None,
        description="Structured remediation explanation if check failed",
    )


class OverallHealthStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILING = "FAILING"
    UNCONFIGURED = "UNCONFIGURED"


class HealthReport(BaseModel):
    """Aggregated health report across network, database, security, and migration checks."""
    status: OverallHealthStatus
    provider: ProviderMetadata
    environment: EnvironmentTier
    postgres_version: Optional[str] = None
    database_name: Optional[str] = None
    active_user: Optional[str] = None
    host: Optional[str] = None
    checks: list[HealthCheckResult] = Field(default_factory=list)
    total_elapsed_ms: float = 0.0
    summary: str = ""

    @property
    def is_healthy(self) -> bool:
        return self.status == OverallHealthStatus.READY

    @property
    def failed_checks(self) -> list[HealthCheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.FAIL]

    @property
    def warning_checks(self) -> list[HealthCheckResult]:
        return [c for c in self.checks if c.status == CheckStatus.WARN]
