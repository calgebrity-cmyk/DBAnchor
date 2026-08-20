"""Schema diff engine comparing application models against live database."""

from __future__ import annotations

from typing import Any
from sqlalchemy import MetaData, Table

from dbanchor.schema.models import (
    DriftReport,
    DriftType,
    SchemaDifference,
    SchemaSnapshot,
    TableSnapshot,
)


def extract_snapshot_from_metadata(metadata: MetaData) -> SchemaSnapshot:
    """Extract SchemaSnapshot from SQLAlchemy MetaData object."""
    from dbanchor.schema.models import ColumnSnapshot, ForeignKeySnapshot, IndexSnapshot

    tables: dict[str, TableSnapshot] = {}
    for tname, table in metadata.tables.items():
        # Clean schema prefix if present
        clean_name = table.name
        cols: dict[str, ColumnSnapshot] = {}
        for col in table.columns:
            cols[col.name] = ColumnSnapshot(
                name=col.name,
                type_str=str(col.type),
                nullable=col.nullable if col.nullable is not None else True,
                default=str(col.default.arg) if col.default is not None else None,
                primary_key=bool(col.primary_key),
            )

        pks = [c.name for c in table.primary_key.columns] if table.primary_key else []

        indexes: list[IndexSnapshot] = []
        for idx in table.indexes:
            indexes.append(
                IndexSnapshot(
                    name=idx.name or "",
                    columns=[c.name for c in idx.columns],
                    unique=bool(idx.unique),
                )
            )

        fks: list[ForeignKeySnapshot] = []
        for fk in table.foreign_keys:
            fks.append(
                ForeignKeySnapshot(
                    name=fk.name,
                    constrained_columns=[fk.parent.name],
                    referred_table=fk.column.table.name,
                    referred_columns=[fk.column.name],
                )
            )

        tables[clean_name] = TableSnapshot(
            name=clean_name,
            columns=cols,
            primary_key=pks,
            indexes=indexes,
            foreign_keys=fks,
        )

    return SchemaSnapshot(tables=tables)


def compare_schemas(
    expected: SchemaSnapshot | MetaData,
    actual: SchemaSnapshot,
) -> DriftReport:
    """Compare expected application schema against actual live database schema."""
    if isinstance(expected, MetaData):
        expected_snap = extract_snapshot_from_metadata(expected)
    else:
        expected_snap = expected

    diffs: list[SchemaDifference] = []
    missing_tables: list[str] = []
    unexpected_tables: list[str] = []
    modified_tables: set[str] = set()

    expected_table_names = set(expected_snap.tables.keys())
    actual_table_names = set(actual.tables.keys())

    # 1. Missing tables (in code models, not in live DB)
    for tname in expected_table_names - actual_table_names:
        missing_tables.append(tname)
        diffs.append(
            SchemaDifference(
                drift_type=DriftType.MISSING_TABLE,
                table_name=tname,
                expected=f"Table '{tname}' defined in application models",
                actual="Table does not exist in live database",
                risk="HIGH: Queries targeting this model will fail with relation does not exist.",
                recommendation=f"Apply pending migrations with 'dbx migrate' or create table '{tname}'.",
            )
        )

    # 2. Unexpected tables (in live DB, not in code models)
    for tname in actual_table_names - expected_table_names:
        # Ignore alembic_version system table
        if tname == "alembic_version":
            continue
        unexpected_tables.append(tname)
        diffs.append(
            SchemaDifference(
                drift_type=DriftType.UNEXPECTED_TABLE,
                table_name=tname,
                expected="Table not defined in application models",
                actual=f"Table '{tname}' exists in live database",
                risk="LOW: Table may belong to another service or legacy feature.",
                recommendation="Verify if this table is managed by another application or adopt it with 'dbx adopt'.",
            )
        )

    # 3. Compare common tables
    common_tables = expected_table_names & actual_table_names
    for tname in common_tables:
        exp_t = expected_snap.tables[tname]
        act_t = actual.tables[tname]

        exp_cols = set(exp_t.columns.keys())
        act_cols = set(act_t.columns.keys())

        # Missing columns
        for cname in exp_cols - act_cols:
            modified_tables.add(tname)
            col_info = exp_t.columns[cname]
            diffs.append(
                SchemaDifference(
                    drift_type=DriftType.MISSING_COLUMN,
                    table_name=tname,
                    column_name=cname,
                    expected=f"{cname} {col_info.type_str} (nullable={col_info.nullable})",
                    actual="Column missing from live table",
                    risk="HIGH: Application queries selecting/inserting this column will fail.",
                    recommendation=f"Generate and run a migration to add column '{cname}' to table '{tname}'.",
                )
            )

        # Unexpected columns
        for cname in act_cols - exp_cols:
            modified_tables.add(tname)
            col_info = act_t.columns[cname]
            diffs.append(
                SchemaDifference(
                    drift_type=DriftType.UNEXPECTED_COLUMN,
                    table_name=tname,
                    column_name=cname,
                    expected="Column not defined in model",
                    actual=f"{cname} {col_info.type_str}",
                    risk="LOW: Column exists in DB but is ignored by application ORM.",
                    recommendation=f"Add column '{cname}' to model definition if needed.",
                )
            )

        # Common columns comparison (types, nullability)
        for cname in exp_cols & act_cols:
            exp_c = exp_t.columns[cname]
            act_c = act_t.columns[cname]

            # Nullability mismatch
            if exp_c.nullable != act_c.nullable:
                modified_tables.add(tname)
                diffs.append(
                    SchemaDifference(
                        drift_type=DriftType.NULLABLE_MISMATCH,
                        table_name=tname,
                        column_name=cname,
                        expected=f"nullable={exp_c.nullable}",
                        actual=f"nullable={act_c.nullable}",
                        risk="MEDIUM: Null constraint violations or unexpected NULL values may occur.",
                        recommendation=f"Align nullability of '{tname}.{cname}' between model and database schema.",
                    )
                )

    has_drift = len(diffs) > 0
    return DriftReport(
        has_drift=has_drift,
        differences=diffs,
        missing_tables=missing_tables,
        unexpected_tables=unexpected_tables,
        modified_tables=sorted(list(modified_tables)),
    )
