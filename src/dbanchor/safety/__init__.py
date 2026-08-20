"""Safety and destructive DDL analysis for DBAnchor."""

from dbanchor.safety.analyzer import analyze_sql_safety
from dbanchor.safety.guard import SafetyGuard, SafetyGuardError
from dbanchor.safety.models import (
    DestructiveOperation,
    OperationType,
    RiskLevel,
    SafetyAssessment,
)

__all__ = [
    "RiskLevel",
    "OperationType",
    "DestructiveOperation",
    "SafetyAssessment",
    "SafetyGuard",
    "SafetyGuardError",
    "analyze_sql_safety",
]
