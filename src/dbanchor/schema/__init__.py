"""Schema inspection and drift detection for DBAnchor."""

from dbanchor.schema.diff import compare_schemas, extract_snapshot_from_metadata
from dbanchor.schema.inspector import SchemaInspector
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

__all__ = [
    "ColumnSnapshot",
    "IndexSnapshot",
    "ForeignKeySnapshot",
    "TableSnapshot",
    "SchemaSnapshot",
    "DriftType",
    "SchemaDifference",
    "DriftReport",
    "SchemaInspector",
    "extract_snapshot_from_metadata",
    "compare_schemas",
]
