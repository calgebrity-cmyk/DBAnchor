"""Integration tests for HealthRunner orchestrator."""

from dbanchor.config.loader import load_config
from dbanchor.connection.url import parse_connection_url
from dbanchor.health.models import CheckStatus, OverallHealthStatus
from dbanchor.health.runner import HealthRunner


def test_health_runner_unconfigured():
    config = load_config(url_override="")
    config.connection.url = None
    runner = HealthRunner(config=config, conn_info=None)
    report = runner.run_health_checks()
    assert report.status == OverallHealthStatus.UNCONFIGURED


def test_health_runner_dns_failure():
    url = "postgresql://user:pass@nonexistent-host-9876543210.invalid:5432/mydb"
    config = load_config(url_override=url)
    conn_info = parse_connection_url(url)
    runner = HealthRunner(config=config, conn_info=conn_info)
    report = runner.run_health_checks()

    assert report.status == OverallHealthStatus.FAILING
    assert any(c.status == CheckStatus.FAIL and c.name == "DNS Resolution" for c in report.checks)
