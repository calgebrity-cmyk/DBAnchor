"""Unit tests for configuration loader and precedence."""

from pathlib import Path
from dbanchor.config.loader import load_config
from dbanchor.environments.detector import EnvironmentTier


def test_load_config_from_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://admin:secret@localhost:5432/testdb")
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DBANCHOR_CONNECT_TIMEOUT", "15")

    cfg = load_config()
    assert cfg.connection.url == "postgresql://admin:secret@localhost:5432/testdb"
    assert cfg.environment == EnvironmentTier.STAGING
    assert cfg.connection.connect_timeout == 15


def test_load_config_url_override():
    cfg = load_config(url_override="postgresql://override:pass@localhost:5432/custom")
    assert cfg.connection.url == "postgresql://override:pass@localhost:5432/custom"
