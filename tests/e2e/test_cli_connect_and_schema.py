"""E2E tests for connect and schema CLI commands with live SQLite engine."""

from typer.testing import CliRunner
from dbanchor.cli.main import app


def test_cli_connect_help(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["connect", "--help"])
    assert result.exit_code == 0
    assert "Verify live database connectivity" in result.stdout


def test_cli_schema_inspect_help(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["schema", "inspect", "--help"])
    assert result.exit_code == 0
    assert "Inspect tables, columns, indexes" in result.stdout


def test_cli_schema_diff_help(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["schema", "diff", "--help"])
    assert result.exit_code == 0
    assert "Compare application models against live database" in result.stdout
