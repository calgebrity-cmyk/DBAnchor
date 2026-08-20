"""Health check implementations for DBAnchor."""

from __future__ import annotations

import socket
import time
from typing import Any, Optional
from sqlalchemy import text

from dbanchor.connection.connector import DatabaseConnector, test_tcp_connectivity
from dbanchor.connection.url import ConnectionInfo
from dbanchor.detection.framework import is_alembic_available, is_sqlalchemy_available
from dbanchor.detection.project import inspect_project_files
from dbanchor.diagnostics.engine import DiagnosticEngine
from dbanchor.health.models import CheckStatus, HealthCheckResult, Severity


def check_dns(conn_info: ConnectionInfo) -> HealthCheckResult:
    """Check DNS resolution for database host."""
    if not conn_info.host:
        return HealthCheckResult(
            name="DNS Resolution",
            status=CheckStatus.FAIL,
            severity=Severity.HIGH,
            message="No host specified in DATABASE_URL",
        )

    start = time.perf_counter()
    try:
        ip = socket.gethostbyname(conn_info.host)
        elapsed = (time.perf_counter() - start) * 1000.0
        return HealthCheckResult(
            name="DNS Resolution",
            status=CheckStatus.PASS,
            severity=Severity.INFO,
            message=f"Resolved '{conn_info.host}' -> {ip}",
            elapsed_ms=elapsed,
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000.0
        diag = DiagnosticEngine.diagnose_error(e, {"host": conn_info.host})
        return HealthCheckResult(
            name="DNS Resolution",
            status=CheckStatus.FAIL,
            severity=Severity.HIGH,
            message=f"Failed to resolve host '{conn_info.host}': {e}",
            elapsed_ms=elapsed,
            diagnostic=diag,
        )


def check_tcp(conn_info: ConnectionInfo, timeout: float = 3.0) -> HealthCheckResult:
    """Check TCP reachability to host:port."""
    if not conn_info.host:
        return HealthCheckResult(
            name="TCP Reachability",
            status=CheckStatus.FAIL,
            severity=Severity.HIGH,
            message="No host specified",
        )

    ok, elapsed, err = test_tcp_connectivity(conn_info.host, conn_info.port, timeout=timeout)
    if ok:
        return HealthCheckResult(
            name="TCP Reachability",
            status=CheckStatus.PASS,
            severity=Severity.INFO,
            message=f"Port {conn_info.port} is reachable ({elapsed:.1f}ms)",
            elapsed_ms=elapsed,
        )
    else:
        diag = DiagnosticEngine.diagnose_error(err or "Connection refused")
        return HealthCheckResult(
            name="TCP Reachability",
            status=CheckStatus.FAIL,
            severity=Severity.HIGH,
            message=f"TCP connection to {conn_info.host}:{conn_info.port} failed: {err}",
            elapsed_ms=elapsed,
            diagnostic=diag,
        )


def check_authentication_and_handshake(
    connector: DatabaseConnector,
    conn_info: ConnectionInfo,
) -> tuple[HealthCheckResult, Optional[dict[str, Any]]]:
    """Test PostgreSQL handshake, authentication, and database access via SQL query."""
    start = time.perf_counter()
    server_info: dict[str, Any] = {}
    try:
        engine = connector.get_sync_engine()
        with engine.connect() as conn:
            # Query version, db, user, and ssl status
            res = conn.execute(
                text(
                    "SELECT version(), current_database(), current_user(), "
                    "(SELECT count(*) FROM pg_extension) as ext_count;"
                )
            ).fetchone()

            if res:
                server_info["version_str"] = res[0]
                server_info["database"] = res[1]
                server_info["user"] = res[2]
                server_info["ext_count"] = res[3]

                # Extract short version e.g. "PostgreSQL 17.0"
                v_full = res[0]
                v_short = v_full.split(",")[0] if "," in v_full else v_full[:30]
                server_info["version_short"] = v_short

        elapsed = (time.perf_counter() - start) * 1000.0
        return (
            HealthCheckResult(
                name="Authentication & Handshake",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message=f"Authenticated as '{server_info.get('user')}' on '{server_info.get('database')}'",
                elapsed_ms=elapsed,
            ),
            server_info,
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000.0
        diag = DiagnosticEngine.diagnose_error(
            e,
            {
                "has_encoding_warning": conn_info.has_encoding_warning,
                "host": conn_info.host,
            },
        )
        return (
            HealthCheckResult(
                name="Authentication & Handshake",
                status=CheckStatus.FAIL,
                severity=Severity.HIGH,
                message=f"Authentication/Handshake failed: {e}",
                elapsed_ms=elapsed,
                diagnostic=diag,
            ),
            None,
        )


def check_permissions(connector: DatabaseConnector) -> HealthCheckResult:
    """Verify DDL and migration schema permissions."""
    start = time.perf_counter()
    try:
        engine = connector.get_sync_engine()
        with engine.connect() as conn:
            res = conn.execute(
                text(
                    "SELECT "
                    "has_schema_privilege(current_user, 'public', 'CREATE'), "
                    "has_schema_privilege(current_user, 'public', 'USAGE');"
                )
            ).fetchone()

            can_create = res[0] if res else False
            can_use = res[1] if res else False

        elapsed = (time.perf_counter() - start) * 1000.0
        if can_create and can_use:
            return HealthCheckResult(
                name="Schema Permissions",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="User has CREATE and USAGE privileges on schema 'public'",
                elapsed_ms=elapsed,
            )
        else:
            return HealthCheckResult(
                name="Schema Permissions",
                status=CheckStatus.WARN,
                severity=Severity.MEDIUM,
                message="User lacks CREATE or USAGE privilege on schema 'public'. Migrations may fail.",
                elapsed_ms=elapsed,
            )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000.0
        return HealthCheckResult(
            name="Schema Permissions",
            status=CheckStatus.WARN,
            severity=Severity.LOW,
            message=f"Could not verify schema permissions: {e}",
            elapsed_ms=elapsed,
        )


def check_application_and_migrations(
    connector: Optional[DatabaseConnector] = None,
) -> HealthCheckResult:
    """Check application migration system and state."""
    start = time.perf_counter()
    project = inspect_project_files()

    if not project.migration_tool:
        elapsed = (time.perf_counter() - start) * 1000.0
        return HealthCheckResult(
            name="Migration System",
            status=CheckStatus.WARN,
            severity=Severity.LOW,
            message="No migration framework detected in project (Alembic / Django).",
            elapsed_ms=elapsed,
        )

    # If Alembic detected and database is reachable, check alembic_version table
    db_rev: Optional[str] = None
    if connector:
        try:
            engine = connector.get_sync_engine()
            with engine.connect() as conn:
                res = conn.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1;")
                ).fetchone()
                if res:
                    db_rev = res[0]
        except Exception:
            pass

    elapsed = (time.perf_counter() - start) * 1000.0
    msg = f"System: {project.migration_tool}"
    if db_rev:
        msg += f" (Current DB revision: {db_rev})"
    else:
        msg += " (No alembic_version table found / fresh database)"

    return HealthCheckResult(
        name="Migration System",
        status=CheckStatus.PASS,
        severity=Severity.INFO,
        message=msg,
        elapsed_ms=elapsed,
    )
