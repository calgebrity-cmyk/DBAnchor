"""E2E test suite exercising all CLI entry point commands."""

import json
from pathlib import Path
from typer.testing import CliRunner
from dbanchor.cli.main import app


def test_cli_init(cli_runner: CliRunner, tmp_path: Path):
    result = cli_runner.invoke(app, ["init", "--dir", str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / ".env").is_file()


def test_cli_status(cli_runner: CliRunner, sample_supabase_url: str):
    result = cli_runner.invoke(app, ["status", "--url", sample_supabase_url])
    assert "System Status" in result.stdout
    assert "Supabase" in result.stdout


def test_cli_config_check(cli_runner: CliRunner, sample_supabase_url: str):
    result = cli_runner.invoke(app, ["config", "check", "--url", sample_supabase_url])
    assert result.exit_code == 0
    assert "Configuration is valid" in result.stdout


def test_cli_config_check_json(cli_runner: CliRunner, sample_supabase_url: str):
    result = cli_runner.invoke(app, ["config", "check", "--url", sample_supabase_url, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["has_url"] is True


def test_cli_provider_detect(cli_runner: CliRunner, sample_neon_url: str):
    result = cli_runner.invoke(app, ["provider", "detect", "--url", sample_neon_url])
    assert result.exit_code == 0
    assert "Neon" in result.stdout


def test_cli_provider_detect_json(cli_runner: CliRunner, sample_neon_url: str):
    result = cli_runner.invoke(app, ["provider", "detect", "--url", sample_neon_url, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["provider_type"] == "neon"


def test_cli_local_status(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["local", "status", "--json"])
    assert result.exit_code in [0, 1]
    data = json.loads(result.stdout)
    assert "docker_available" in data
