"""Schema snapshot and drift models for DBAnchor."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ColumnSnapshot(BaseModel):
    """Snapshot of a database table column."""
    name: str
    type_str: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False
    unique: bool = False


class IndexSnapshot(BaseModel):
    """Snapshot of a table index."""
    name: str
    columns: list[str]
    unique: bool = False


class ForeignKeySnapshot(BaseModel):
    """Snapshot of a foreign key constraint."""
    name: Optional[str] = None
    constrained_columns: list[str]
    referred_table: str
    referred_columns: list[str]


class TableSnapshot(BaseModel):
    """Snapshot of a database table structure."""
    name: str
    columns: dict[str, ColumnSnapshot] = Field(default_factory=dict)
    primary_key: list[str] = Field(default_factory=list)
    indexes: list[IndexSnapshot] = Field(default_factory=list)
    foreign_keys: list[ForeignKeySnapshot] = Field(default_factory=list)


class SchemaSnapshot(BaseModel):
    """Complete snapshot of a database schema."""
    tables: dict[str, TableSnapshot] = Field(default_factory=dict)
    enums: list[str] = Field(default_factory=list)
    views: list[str] = Field(default_factory=list)


class DriftType(str, Enum):
    MISSING_TABLE = "MISSING_TABLE"
    UNEXPECTED_TABLE = "UNEXPECTED_TABLE"
    MISSING_COLUMN = "MISSING_COLUMN"
    UNEXPECTED_COLUMN = "UNEXPECTED_COLUMN"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    NULLABLE_MISMATCH = "NULLABLE_MISMATCH"
    MISSING_INDEX = "MISSING_INDEX"
    UNEXPECTED_INDEX = "UNEXPECTED_INDEX"


class SchemaDifference(BaseModel):
    """An individual difference between expected application schema and live database."""
    drift_type: DriftType
    table_name: str
    column_name: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    risk: str = Field(description="Risk assessment of this difference")
    recommendation: str = Field(description="Actionable fix recommendation")


class DriftReport(BaseModel):
    """Comprehensive schema drift analysis report."""
    has_drift: bool = False
    differences: list[SchemaDifference] = Field(default_factory=list)
    missing_tables: list[str] = Field(default_factory=list)
    unexpected_tables: list[str] = Field(default_factory=list)
    modified_tables: list[str] = Field(default_factory=list)

    @property
    def total_differences(self) -> int:
        return len(self.differences)
