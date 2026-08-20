"""Unit tests for JSON formatter and serialization."""

import json
from dbanchor.environments.detector import EnvironmentTier
from dbanchor.health.models import (
    CheckStatus,
    HealthCheckResult,
    HealthReport,
    OverallHealthStatus,
    Severity,
)
from dbanchor.output.json_formatter import to_json
from dbanchor.providers.models import ProviderMetadata, ProviderType


def test_to_json_health_report():
    report = HealthReport(
        status=OverallHealthStatus.READY,
        provider=ProviderMetadata(name="Supabase", provider_type=ProviderType.SUPABASE, requires_ssl=True),
        environment=EnvironmentTier.DEVELOPMENT,
        host="db.supabase.co",
        checks=[
            HealthCheckResult(
                name="DNS",
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="DNS OK",
                elapsed_ms=1.5,
            )
        ],
    )

    json_str = to_json(report)
    data = json.loads(json_str)
    assert data["status"] == "READY"
    assert data["provider"]["name"] == "Supabase"
    assert data["checks"][0]["status"] == "PASS"
