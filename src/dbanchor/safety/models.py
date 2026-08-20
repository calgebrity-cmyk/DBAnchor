"""Safety assessment models for DDL operations."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def color(self) -> str:
        if self == RiskLevel.LOW:
            return "green"
        if self == RiskLevel.MEDIUM:
            return "yellow"
        if self == RiskLevel.HIGH:
            return "bold red"
        return "bold red on black"


class OperationType(str, Enum):
    CREATE_TABLE = "CREATE_TABLE"
    ADD_COLUMN = "ADD_COLUMN"
    DROP_COLUMN = "DROP_COLUMN"
    DROP_TABLE = "DROP_TABLE"
    ALTER_TYPE = "ALTER_TYPE"
    TRUNCATE = "TRUNCATE"
    CREATE_INDEX = "CREATE_INDEX"
    DROP_INDEX = "DROP_INDEX"
    ADD_CONSTRAINT = "ADD_CONSTRAINT"
    DROP_CONSTRAINT = "DROP_CONSTRAINT"
    RAW_SQL = "RAW_SQL"


class DestructiveOperation(BaseModel):
    """Specific destructive DDL operation flagged during safety review."""
    operation_type: OperationType
    target_object: str = Field(description="Target table, column, or constraint")
    sql_snippet: str = Field(description="SQL code or migration operation")
    risk_level: RiskLevel
    reason: str = Field(description="Explanation of potential data loss or locking risk")


class SafetyAssessment(BaseModel):
    """Aggregate safety assessment of proposed database changes."""
    overall_risk: RiskLevel = RiskLevel.LOW
    is_destructive: bool = False
    operations: list[DestructiveOperation] = Field(default_factory=list)
    can_auto_execute: bool = True
    warnings: list[str] = Field(default_factory=list)

    @property
    def has_critical_operations(self) -> bool:
        return self.overall_risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}
