"""Integration tests for SchemaInspector using SQLite test database."""

from dbanchor.schema.inspector import SchemaInspector


def test_schema_inspector_reflects_tables(mock_sqlite_engine):
    inspector = SchemaInspector(mock_sqlite_engine)
    snapshot = inspector.inspect_schema()

    assert "users" in snapshot.tables
    assert "posts" in snapshot.tables

    users_tbl = snapshot.tables["users"]
    assert "id" in users_tbl.columns
    assert "username" in users_tbl.columns
    assert "email" in users_tbl.columns
    assert users_tbl.columns["username"].nullable is False
    assert users_tbl.columns["id"].primary_key is True
