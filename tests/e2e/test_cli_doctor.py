"""E2E tests for dbx doctor CLI command."""

import json
from typer.testing import CliRunner
from dbanchor.cli.main import app


def test_cli_doctor_unconfigured(cli_runner: CliRunner, monkeypatch):
    for k in ["DATABASE_URL", "DB_URL", "POSTGRES_URL"]:
        monkeypatch.delenv(k, raising=False)

    result = cli_runner.invoke(app, ["doctor", "--json"])
    assert result.exit_code in [0, 1]
    data = json.loads(result.stdout)
    assert data["status"] in ["UNCONFIGURED", "FAILING"]


def test_cli_doctor_human_output(cli_runner: CliRunner, sample_supabase_url: str):
    result = cli_runner.invoke(app, ["doctor", "--url", sample_supabase_url])
    assert "DBAnchor Database Doctor" in result.stdout
    assert "Supabase" in result.stdout


def test_cli_version(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "DBAnchor" in result.stdout
    assert "0.1.0" in result.stdout
