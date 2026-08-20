"""E2E tests for dbx migrate and migration subcommands."""

from typer.testing import CliRunner
from dbanchor.cli.main import app


def test_cli_migration_status(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["migration", "status"])
    assert "Alembic Migration Status" in result.stdout


def test_cli_migration_plan(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["migration", "plan"])
    assert "DBAnchor Migration Engine" in result.stdout or "already up to date" in result.stdout


def test_cli_migration_explain(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["migration", "explain", "Multiple heads are present"])
    assert result.exit_code == 0
    assert "Explanation" in result.stdout
    assert "Alembic Multiple Migration Heads Detected" in result.stdout
