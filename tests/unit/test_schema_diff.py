"""Unit tests for schema reflection and drift detection."""

from sqlalchemy import Column, Integer, MetaData, String, Table
from dbanchor.schema.diff import compare_schemas, extract_snapshot_from_metadata
from dbanchor.schema.models import (
    ColumnSnapshot,
    DriftType,
    SchemaSnapshot,
    TableSnapshot,
)


def test_compare_identical_schemas():
    meta = MetaData()
    users = Table(
        "users",
        meta,
        Column("id", Integer, primary_key=True),
        Column("username", String(50), nullable=False),
    )
    snap = extract_snapshot_from_metadata(meta)
    report = compare_schemas(meta, snap)
    assert report.has_drift is False
    assert len(report.differences) == 0


def test_detect_missing_table_in_database():
    meta = MetaData()
    Table("orders", meta, Column("id", Integer, primary_key=True))
    empty_snap = SchemaSnapshot(tables={})

    report = compare_schemas(meta, empty_snap)
    assert report.has_drift is True
    assert "orders" in report.missing_tables
    assert any(d.drift_type == DriftType.MISSING_TABLE for d in report.differences)


def test_detect_missing_column_in_database():
    meta = MetaData()
    Table("users", meta, Column("id", Integer, primary_key=True), Column("email", String(100)))

    # Live snapshot only has 'id'
    live_snap = SchemaSnapshot(
        tables={
            "users": TableSnapshot(
                name="users",
                columns={"id": ColumnSnapshot(name="id", type_str="INTEGER", nullable=False, primary_key=True)},
            )
        }
    )

    report = compare_schemas(meta, live_snap)
    assert report.has_drift is True
    assert any(d.drift_type == DriftType.MISSING_COLUMN and d.column_name == "email" for d in report.differences)
