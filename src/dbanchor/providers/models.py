"""Provider metadata models for DBAnchor."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    SUPABASE = "supabase"
    NEON = "neon"
    RAILWAY = "railway"
    AWS_RDS = "aws_rds"
    GCP_CLOUDSQL = "gcp_cloudsql"
    AZURE_POSTGRES = "azure_postgres"
    DOCKER = "docker"
    LOCALHOST = "localhost"
    GENERIC = "generic"


class ProviderMetadata(BaseModel):
    """Informational metadata about detected database provider."""
    name: str = Field(description="Human-readable provider name")
    provider_type: ProviderType = Field(description="Enum classification")
    is_serverless: bool = Field(default=False, description="Serverless auto-suspend architecture")
    requires_ssl: bool = Field(default=False, description="Whether SSL is strictly mandated by provider")
    is_connection_pooled: bool = Field(default=False, description="Whether this endpoint is a connection pooler (e.g. PgBouncer)")
    recommendations: list[str] = Field(default_factory=list, description="Provider-specific tips and best practices")
