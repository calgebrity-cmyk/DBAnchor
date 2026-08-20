"""Configuration models for DBAnchor."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from dbanchor.environments.detector import EnvironmentTier


class ConnectionConfig(BaseModel):
    """Database connection and pool settings."""
    url: Optional[str] = Field(default=None, description="Database connection URL")
    connect_timeout: int = Field(default=10, description="Socket connect timeout in seconds")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum pool overflow")
    pool_recycle: int = Field(default=1800, description="Recycle connections after N seconds")
    pool_pre_ping: bool = Field(default=True, description="Ping connection on checkout")
    echo: bool = Field(default=False, description="Log raw SQL queries")


class MigrationConfig(BaseModel):
    """Migration management settings."""
    auto_apply_dev: bool = Field(default=True, description="Auto apply migrations in development")
    directory: Optional[str] = Field(default=None, description="Custom migrations directory path")
    alembic_ini: Optional[str] = Field(default=None, description="Path to alembic.ini")


class SafetyConfig(BaseModel):
    """Safety guardrails settings."""
    allow_destructive: bool = Field(
        default=False,
        description="Allow destructive DDL operations without explicit approval",
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require interactive confirmation for production changes",
    )
    dry_run_first: bool = Field(
        default=True,
        description="Always generate a dry-run plan before applying migrations",
    )


class DBAnchorConfig(BaseModel):
    """Root configuration object for DBAnchor."""
    environment: EnvironmentTier = Field(
        default=EnvironmentTier.UNKNOWN,
        description="Application environment tier",
    )
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    migrations: MigrationConfig = Field(default_factory=MigrationConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
