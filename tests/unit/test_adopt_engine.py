"""Unit tests for the project adoption engine."""

from pathlib import Path
from dbanchor.config.models import ConnectionConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.connection.url import parse_connection_url
from dbanchor.migrations.adopt import adopt_project, plan_adoption


def test_plan_adoption(mock_sqlite_engine, tmp_path: Path):
    # Wrap engine in connector
    info = parse_connection_url("postgresql://user:pass@localhost:5432/test")
    connector = DatabaseConnector(ConnectionConfig(url="postgresql://user:pass@localhost:5432/test"), info)
    connector._sync_engine = mock_sqlite_engine

    plan = plan_adoption(connector, project_root=tmp_path)
    assert plan.table_count >= 2
    assert "users" in plan.tables
    assert len(plan.steps) > 0


def test_adopt_project_creates_structure(mock_sqlite_engine, tmp_path: Path):
    info = parse_connection_url("postgresql://user:pass@localhost:5432/test")
    connector = DatabaseConnector(ConnectionConfig(url="postgresql://user:pass@localhost:5432/test"), info)
    connector._sync_engine = mock_sqlite_engine

    res = adopt_project(connector, project_root=tmp_path)
    assert res.success is True
    assert (tmp_path / "alembic.ini").is_file()
    assert (tmp_path / "migrations" / "env.py").is_file()
    assert (tmp_path / "migrations" / "versions").is_dir()
