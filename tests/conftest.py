"""Pytest configuration and shared fixtures for DBAnchor tests."""

from __future__ import annotations

import os
from pathlib import Path
import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from typer.testing import CliRunner

from dbanchor.config.models import ConnectionConfig, DBAnchorConfig, MigrationConfig, SafetyConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.connection.url import parse_connection_url
from dbanchor.core.database import Database
from dbanchor.environments.detector import EnvironmentTier


@pytest.fixture
def cli_runner() -> CliRunner:
    """Typer CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_sqlite_engine(tmp_path: Path):
    """Provide a real SQLite engine for schema inspection and reflection tests."""
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")

    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("username", String(50), nullable=False),
        Column("email", String(100), nullable=True),
    )
    posts = Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200), nullable=False),
        Column("content", String, nullable=True),
    )
    metadata.create_all(engine)
    return engine


@pytest.fixture
def sample_connection_url() -> str:
    return "postgresql://postgres:secretpassword@localhost:5432/testdb"


@pytest.fixture
def sample_supabase_url() -> str:
    return "postgresql://postgres:mypassword@db.xyz.supabase.co:5432/postgres?sslmode=require"


@pytest.fixture
def sample_neon_url() -> str:
    return "postgresql://neondb_owner:mypass@ep-cool-fog-12345.us-east-2.aws.neon.tech/neondb?sslmode=require"


@pytest.fixture
def sample_unencoded_url() -> str:
    return "postgresql://user:pass@word@localhost:5432/mydb"
