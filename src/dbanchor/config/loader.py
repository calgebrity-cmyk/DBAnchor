"""Configuration loader supporting .env, TOML files, and environment variables."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import find_dotenv, load_dotenv

from dbanchor.config.models import (
    ConnectionConfig,
    DBAnchorConfig,
    MigrationConfig,
    SafetyConfig,
)
from dbanchor.environments.detector import detect_environment


def find_config_file(start_path: Path | None = None) -> Optional[Path]:
    """Locate dbanchor.toml, dbx.toml, or pyproject.toml in start_path or parents."""
    curr = start_path or Path.cwd()
    for directory in [curr, *curr.parents]:
        for candidate in ["dbanchor.toml", "dbx.toml", "pyproject.toml"]:
            file_path = directory / candidate
            if file_path.is_file():
                return file_path
    return None


def load_toml_config(file_path: Path) -> dict[str, Any]:
    """Parse TOML configuration from pyproject.toml or dbx.toml."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # Fallback for Python 3.10
        except ImportError:
            return {}

    try:
        with open(file_path, "rb") as f:
            data = tomllib.load(f)

        if file_path.name == "pyproject.toml":
            return data.get("tool", {}).get("dbanchor", data.get("tool", {}).get("dbx", {}))
        elif file_path.name in {"dbanchor.toml", "dbx.toml"}:
            return data.get("dbanchor", data.get("dbx", data))
    except Exception:
        pass
    return {}


def load_config(
    env_file: Optional[str | Path] = None,
    url_override: Optional[str] = None,
    env_tier_override: Optional[str] = None,
) -> DBAnchorConfig:
    """Load DBAnchor configuration with precedence:

    1. Function arguments / CLI overrides
    2. Environment variables (DATABASE_URL, APP_ENV, etc.)
    3. .env file
    4. dbanchor.toml / dbx.toml / pyproject.toml
    5. Default values
    """
    # 1. Load .env file
    if env_file:
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        found_env = find_dotenv(usecwd=True)
        if found_env:
            load_dotenv(dotenv_path=found_env, override=False)

    # 2. Check for TOML config
    toml_data: dict[str, Any] = {}
    config_file = find_config_file()
    if config_file:
        toml_data = load_toml_config(config_file)

    conn_toml = toml_data.get("connection", {})
    mig_toml = toml_data.get("migrations", {})
    safety_toml = toml_data.get("safety", {})

    # 3. Resolve DATABASE_URL from various env keys
    db_url = (
        url_override
        or os.getenv("DATABASE_URL")
        or os.getenv("DB_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("POSTGRESQL_URL")
        or conn_toml.get("url")
    )

    # 4. Resolve connection settings
    connect_timeout = int(
        os.getenv("DBANCHOR_CONNECT_TIMEOUT")
        or os.getenv("DBX_CONNECT_TIMEOUT")
        or conn_toml.get("connect_timeout", 10)
    )
    pool_size = int(
        os.getenv("DBANCHOR_POOL_SIZE")
        or os.getenv("DBX_POOL_SIZE")
        or conn_toml.get("pool_size", 5)
    )
    max_overflow = int(
        os.getenv("DBANCHOR_MAX_OVERFLOW")
        or os.getenv("DBX_MAX_OVERFLOW")
        or conn_toml.get("max_overflow", 10)
    )
    pool_recycle = int(
        os.getenv("DBANCHOR_POOL_RECYCLE")
        or conn_toml.get("pool_recycle", 1800)
    )
    pool_pre_ping = (
        os.getenv("DBANCHOR_POOL_PRE_PING", "true").lower() == "true"
        if "DBANCHOR_POOL_PRE_PING" in os.environ
        else conn_toml.get("pool_pre_ping", True)
    )
    echo = (
        os.getenv("DBANCHOR_ECHO", "false").lower() == "true"
        if "DBANCHOR_ECHO" in os.environ
        else conn_toml.get("echo", False)
    )

    # 5. Resolve migration settings
    auto_apply_dev = (
        os.getenv("DBANCHOR_AUTO_APPLY", "true").lower() == "true"
        if "DBANCHOR_AUTO_APPLY" in os.environ
        else mig_toml.get("auto_apply_dev", True)
    )
    migration_dir = os.getenv("DBANCHOR_MIGRATION_DIR") or mig_toml.get("directory")
    alembic_ini = os.getenv("DBANCHOR_ALEMBIC_INI") or mig_toml.get("alembic_ini")

    # 6. Resolve safety settings
    allow_destructive = (
        os.getenv("DBANCHOR_ALLOW_DESTRUCTIVE", "false").lower() == "true"
        if "DBANCHOR_ALLOW_DESTRUCTIVE" in os.environ
        else safety_toml.get("allow_destructive", False)
    )
    require_confirmation = (
        os.getenv("DBANCHOR_REQUIRE_CONFIRMATION", "true").lower() == "true"
        if "DBANCHOR_REQUIRE_CONFIRMATION" in os.environ
        else safety_toml.get("require_confirmation", True)
    )
    dry_run_first = (
        os.getenv("DBANCHOR_DRY_RUN_FIRST", "true").lower() == "true"
        if "DBANCHOR_DRY_RUN_FIRST" in os.environ
        else safety_toml.get("dry_run_first", True)
    )

    # 7. Environment tier
    if env_tier_override:
        tier = detect_environment()
        # if override given, try parse
        for candidate in ["development", "test", "staging", "production"]:
            if candidate in env_tier_override.lower():
                from dbanchor.environments.detector import EnvironmentTier
                tier = EnvironmentTier(candidate)
                break
    else:
        tier = detect_environment()

    return DBAnchorConfig(
        environment=tier,
        connection=ConnectionConfig(
            url=db_url,
            connect_timeout=connect_timeout,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            echo=echo,
        ),
        migrations=MigrationConfig(
            auto_apply_dev=auto_apply_dev,
            directory=migration_dir,
            alembic_ini=alembic_ini,
        ),
        safety=SafetyConfig(
            allow_destructive=allow_destructive,
            require_confirmation=require_confirmation,
            dry_run_first=dry_run_first,
        ),
    )
