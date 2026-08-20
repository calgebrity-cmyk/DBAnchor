"""Health check runner for DBAnchor."""

from __future__ import annotations

import time
from typing import Optional

from dbanchor.config.models import DBAnchorConfig
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.connection.url import ConnectionInfo, parse_connection_url
from dbanchor.environments.detector import detect_environment
from dbanchor.health.checks import (
    check_application_and_migrations,
    check_authentication_and_handshake,
    check_dns,
    check_permissions,
    check_tcp,
)
from dbanchor.health.models import (
    CheckStatus,
    HealthCheckResult,
    HealthReport,
    OverallHealthStatus,
    Severity,
)
from dbanchor.providers.detector import detect_provider


class HealthRunner:
    """Orchestrates comprehensive, non-destructive health checks."""

    def __init__(
        self,
        config: DBAnchorConfig,
        conn_info: Optional[ConnectionInfo] = None,
        connector: Optional[DatabaseConnector] = None,
    ) -> None:
        self.config = config
        self.conn_info = conn_info
        if self.conn_info is None and self.config.connection.url:
            self.conn_info = parse_connection_url(self.config.connection.url)
        self.connector = connector
        if self.connector is None and self.conn_info:
            self.connector = DatabaseConnector(self.config.connection, self.conn_info)

    def run_health_checks(self) -> HealthReport:
        """Run all structured health checks and return aggregated HealthReport."""
        start_all = time.perf_counter()
        checks: list[HealthCheckResult] = []

        # 0. Check if DATABASE_URL is configured
        if not self.conn_info or not self.conn_info.raw_url:
            total_time = (time.perf_counter() - start_all) * 1000.0
            return HealthReport(
                status=OverallHealthStatus.UNCONFIGURED,
                provider=detect_provider(None),
                environment=detect_environment(),
                summary="DATABASE_URL is not configured in .env or environment variables.",
                checks=[
                    HealthCheckResult(
                        name="Configuration",
                        status=CheckStatus.FAIL,
                        severity=Severity.HIGH,
                        message="DATABASE_URL missing. Add DATABASE_URL to .env",
                    )
                ],
                total_elapsed_ms=total_time,
            )

        provider = detect_provider(self.conn_info)
        environment = self.config.environment if self.config.environment != "unknown" else detect_environment(self.conn_info.host)

        # 1. DNS Check
        dns_res = check_dns(self.conn_info)
        checks.append(dns_res)

        # If DNS fails, skip subsequent network checks
        if dns_res.status == CheckStatus.FAIL:
            total_time = (time.perf_counter() - start_all) * 1000.0
            return HealthReport(
                status=OverallHealthStatus.FAILING,
                provider=provider,
                environment=environment,
                host=self.conn_info.host,
                checks=checks,
                total_elapsed_ms=total_time,
                summary=f"Database host '{self.conn_info.host}' could not be reached (DNS failure).",
            )

        # 2. TCP Port Check
        tcp_res = check_tcp(self.conn_info, timeout=float(self.config.connection.connect_timeout))
        checks.append(tcp_res)

        if tcp_res.status == CheckStatus.FAIL:
            total_time = (time.perf_counter() - start_all) * 1000.0
            return HealthReport(
                status=OverallHealthStatus.FAILING,
                provider=provider,
                environment=environment,
                host=self.conn_info.host,
                checks=checks,
                total_elapsed_ms=total_time,
                summary=f"Database port {self.conn_info.port} on '{self.conn_info.host}' is closed or unreachable.",
            )

        # 3. Authentication & Handshake Check
        server_info: dict = {}
        if self.connector:
            auth_res, s_info = check_authentication_and_handshake(self.connector, self.conn_info)
            checks.append(auth_res)
            if s_info:
                server_info = s_info

            if auth_res.status == CheckStatus.FAIL:
                total_time = (time.perf_counter() - start_all) * 1000.0
                return HealthReport(
                    status=OverallHealthStatus.FAILING,
                    provider=provider,
                    environment=environment,
                    host=self.conn_info.host,
                    checks=checks,
                    total_elapsed_ms=total_time,
                    summary="Database is reachable but authentication failed. Check credentials in DATABASE_URL.",
                )

            # 4. Schema Permissions Check
            perm_res = check_permissions(self.connector)
            checks.append(perm_res)

        # 5. Application & Migration System Check
        mig_res = check_application_and_migrations(self.connector)
        checks.append(mig_res)

        # Compute overall status
        has_failures = any(c.status == CheckStatus.FAIL for c in checks)
        has_warnings = any(c.status == CheckStatus.WARN for c in checks)

        if has_failures:
            overall = OverallHealthStatus.FAILING
            summary = "One or more critical database health checks failed."
        elif has_warnings:
            overall = OverallHealthStatus.DEGRADED
            summary = "Database is connected with minor warnings."
        else:
            overall = OverallHealthStatus.READY
            summary = "Database is healthy and ready for application traffic."

        total_time = (time.perf_counter() - start_all) * 1000.0
        return HealthReport(
            status=overall,
            provider=provider,
            environment=environment,
            postgres_version=server_info.get("version_short"),
            database_name=server_info.get("database") or self.conn_info.database,
            active_user=server_info.get("user") or self.conn_info.username,
            host=self.conn_info.host,
            checks=checks,
            total_elapsed_ms=total_time,
            summary=summary,
        )
