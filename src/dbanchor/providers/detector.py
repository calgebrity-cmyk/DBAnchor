"""Provider detector for PostgreSQL hosting platforms."""

from __future__ import annotations

import os
from typing import Optional
from dbanchor.connection.url import ConnectionInfo
from dbanchor.providers.models import ProviderMetadata, ProviderType


def detect_provider(conn_info: ConnectionInfo | None) -> ProviderMetadata:
    """Detect database provider platform from hostname, port, username, and query params.

    Does not require provider proprietary SDKs.
    """
    if conn_info is None or not conn_info.host:
        return ProviderMetadata(
            name="Generic PostgreSQL",
            provider_type=ProviderType.GENERIC,
            is_serverless=False,
            requires_ssl=False,
            is_connection_pooled=False,
            recommendations=["Ensure PostgreSQL is configured with standard best practices."],
        )

    host = conn_info.host.lower()
    port = conn_info.port

    # 1. Supabase
    if "supabase.co" in host or "supabase.com" in host or "pooler.supabase.com" in host:
        is_pooled = port == 6543 or "pooler" in host
        recs = [
            "Supabase mandates SSL connections (?sslmode=require).",
        ]
        if is_pooled:
            recs.append(
                "Transaction pooler port (6543) detected. Note: Prepared statements / Alembic migrations should use direct port 5432 or session mode."
            )
        return ProviderMetadata(
            name="Supabase",
            provider_type=ProviderType.SUPABASE,
            is_serverless=True,
            requires_ssl=True,
            is_connection_pooled=is_pooled,
            recommendations=recs,
        )

    # 2. Neon
    if "neon.tech" in host or "aws.neon.tech" in host:
        is_pooled = "-pooler" in host or port == 6543
        return ProviderMetadata(
            name="Neon",
            provider_type=ProviderType.NEON,
            is_serverless=True,
            requires_ssl=True,
            is_connection_pooled=is_pooled,
            recommendations=[
                "Neon requires SSL (?sslmode=require).",
                "Neon automatically suspends inactive databases; first connection might have slight cold-start latency.",
            ],
        )

    # 3. Railway
    if "railway.app" in host or "railway.internal" in host or "rlwy.net" in host or os.getenv("RAILWAY_ENVIRONMENT"):
        return ProviderMetadata(
            name="Railway",
            provider_type=ProviderType.RAILWAY,
            is_serverless=False,
            requires_ssl=False,
            is_connection_pooled=False,
            recommendations=[
                "Railway private networking (railway.internal) is faster when communicating between services within Railway.",
            ],
        )

    # 4. AWS RDS / Aurora
    if "rds.amazonaws.com" in host:
        is_aurora = "aurora" in host
        name = "AWS Aurora PostgreSQL" if is_aurora else "AWS RDS PostgreSQL"
        return ProviderMetadata(
            name=name,
            provider_type=ProviderType.AWS_RDS,
            is_serverless=is_aurora,
            requires_ssl=True,
            is_connection_pooled=False,
            recommendations=[
                "Ensure RDS Security Group allows inbound TCP traffic on port 5432 from your application IP / VPC CIDR.",
            ],
        )

    # 5. GCP Cloud SQL
    if "cloudsql.goog" in host or "/cloudsql/" in (conn_info.raw_url or ""):
        return ProviderMetadata(
            name="Google Cloud SQL",
            provider_type=ProviderType.GCP_CLOUDSQL,
            is_serverless=False,
            requires_ssl=True,
            is_connection_pooled=False,
            recommendations=[
                "For production, prefer connecting via Cloud SQL Auth Proxy for IAM-based security without managing IP allowlists.",
            ],
        )

    # 6. Azure PostgreSQL
    if "postgres.database.azure.com" in host:
        return ProviderMetadata(
            name="Azure Database for PostgreSQL",
            provider_type=ProviderType.AZURE_POSTGRES,
            is_serverless=False,
            requires_ssl=True,
            is_connection_pooled=False,
            recommendations=[
                "Ensure Azure PostgreSQL firewall rule allows your client IP address.",
            ],
        )

    # 7. Localhost / Docker
    if host in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}:
        is_docker = host == "host.docker.internal" or os.path.exists("/.dockerenv")
        name = "Docker PostgreSQL" if is_docker else "Localhost PostgreSQL"
        ptype = ProviderType.DOCKER if is_docker else ProviderType.LOCALHOST
        return ProviderMetadata(
            name=name,
            provider_type=ptype,
            is_serverless=False,
            requires_ssl=False,
            is_connection_pooled=False,
            recommendations=[
                "Running in local environment. Safe development migrations are enabled.",
            ],
        )

    # 8. Generic
    return ProviderMetadata(
        name="Generic PostgreSQL",
        provider_type=ProviderType.GENERIC,
        is_serverless=False,
        requires_ssl=False,
        is_connection_pooled=False,
        recommendations=["Standard PostgreSQL instance detected."],
    )
