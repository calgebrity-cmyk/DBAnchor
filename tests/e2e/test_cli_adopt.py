"""E2E tests for dbx adopt command."""

from typer.testing import CliRunner
from dbanchor.cli.main import app


def test_cli_adopt_help(cli_runner: CliRunner):
    result = cli_runner.invoke(app, ["adopt", "--help"])
    assert result.exit_code == 0
    assert "Adopt an existing unmanaged database" in result.stdout
