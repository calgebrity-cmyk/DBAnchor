"""Main Typer CLI application entry point for DBAnchor / dbx."""

from __future__ import annotations

from typing import Optional
import typer

from dbanchor.cli.adopt_cmd import run_adopt
from dbanchor.cli.config_cmd import run_config_check
from dbanchor.cli.connect_cmd import run_connect
from dbanchor.cli.doctor_cmd import run_doctor
from dbanchor.cli.init_cmd import run_init
from dbanchor.cli.local_cmd import (
    run_local_reset,
    run_local_start,
    run_local_status,
    run_local_stop,
)
from dbanchor.cli.migrate_cmd import (
    run_migrate,
    run_migration_explain,
    run_migration_status,
)
from dbanchor.cli.provider_cmd import run_provider_detect
from dbanchor.cli.schema_cmd import run_schema_diff, run_schema_inspect
from dbanchor.cli.status_cmd import run_status
from dbanchor.cli.version_cmd import run_version

app = typer.Typer(
    name="dbanchor",
    help="DBAnchor -- Safe Universal Database Developer-Experience Middleware & Diagnostics.",
    no_args_is_help=True,
    add_completion=False,
)

migration_app = typer.Typer(help="Manage and inspect Alembic database migrations.")
schema_app = typer.Typer(help="Inspect schema and detect drift against application models.")
config_app = typer.Typer(help="Validate and check database configuration.")
provider_app = typer.Typer(help="Detect database hosting provider.")
local_app = typer.Typer(help="Manage local Docker PostgreSQL instance.")

app.add_typer(migration_app, name="migration")
app.add_typer(schema_app, name="schema")
app.add_typer(config_app, name="config")
app.add_typer(provider_app, name="provider")
app.add_typer(local_app, name="local")


# ==============================================================================
# Top-level Commands
# ==============================================================================


@app.command("doctor")
def doctor(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose diagnostics"),
) -> None:
    """Diagnose database connectivity, credentials, SSL, permissions, and migration health."""
    code = run_doctor(env_file=env_file, url=url, as_json=json_output, verbose=verbose)
    if code != 0:
        raise typer.Exit(code)


@app.command("init")
def init(
    project_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="Project directory"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Inspect local project structure and initialize DBAnchor configuration."""
    code = run_init(project_dir=project_dir, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@app.command("connect")
def connect(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Verify live database connectivity and ping latency."""
    code = run_connect(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@app.command("status")
def status(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Show an instant high-level status card of the database and migrations."""
    code = run_status(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@app.command("migrate")
def migrate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview plan without executing"),
    force_destructive: bool = typer.Option(False, "--force-destructive", help="Explicitly allow destructive changes"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Safely apply pending migrations to the database."""
    code = run_migrate(
        dry_run=dry_run,
        force_destructive=force_destructive,
        yes=yes,
        env_file=env_file,
        url=url,
        as_json=json_output,
    )
    if code != 0:
        raise typer.Exit(code)


@app.command("adopt")
def adopt(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Adopt an existing unmanaged database into DBAnchor without data loss."""
    code = run_adopt(env_file=env_file, url=url, yes=yes, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@app.command("version")
def version(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Show DBAnchor version and installed driver capabilities."""
    code = run_version(as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


# ==============================================================================
# Migration Subcommands
# ==============================================================================


@migration_app.command("status")
def migration_status(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Show current database revision and pending migration count."""
    code = run_migration_status(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@migration_app.command("plan")
def migration_plan(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Generate dry-run migration plan and safety risk assessment."""
    code = run_migrate(dry_run=True, env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@migration_app.command("explain")
def migration_explain(
    error_or_revision: Optional[str] = typer.Argument(None, help="Error message or revision ID to explain"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Explain migration error conditions or divergence causes."""
    code = run_migration_explain(error_or_revision=error_or_revision, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@migration_app.command("verify")
def migration_verify(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Verify that the database is fully up to date with codebase heads."""
    code = run_migration_status(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


# ==============================================================================
# Schema Subcommands
# ==============================================================================


@schema_app.command("inspect")
def schema_inspect(
    table: Optional[str] = typer.Option(None, "--table", "-t", help="Specific table name to inspect"),
    schema: str = typer.Option("public", "--schema", "-s", help="PostgreSQL schema name"),
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Inspect tables, columns, indexes, and constraints in the live database."""
    code = run_schema_inspect(table_name=table, schema=schema, env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@schema_app.command("diff")
def schema_diff(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Compare application models against live database to detect schema drift."""
    code = run_schema_diff(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


# ==============================================================================
# Config Subcommands
# ==============================================================================


@config_app.command("check")
def config_check(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Validate database configuration, timeouts, and URL encoding."""
    code = run_config_check(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


# ==============================================================================
# Provider Subcommands
# ==============================================================================


@provider_app.command("detect")
def provider_detect(
    env_file: Optional[str] = typer.Option(None, "--env-file", "-e", help="Path to .env file"),
    url: Optional[str] = typer.Option(None, "--url", "-u", help="DATABASE_URL override"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Detect database hosting provider (Supabase, Neon, Railway, RDS, etc.)."""
    code = run_provider_detect(env_file=env_file, url=url, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


# ==============================================================================
# Local Docker Subcommands
# ==============================================================================


@local_app.command("start")
def local_start(
    port: int = typer.Option(5432, "--port", "-p", help="Host port to bind"),
    database: str = typer.Option("app_db", "--db", "-d", help="Database name"),
    user: str = typer.Option("postgres", "--user", "-u", help="Database username"),
    password: str = typer.Option("postgres", "--password", help="Database password"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Start local PostgreSQL in Docker container."""
    code = run_local_start(port=port, database=database, user=user, password=password, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@local_app.command("stop")
def local_stop(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Stop local PostgreSQL Docker container."""
    code = run_local_stop(as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@local_app.command("reset")
def local_reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Reset and delete local PostgreSQL Docker container."""
    code = run_local_reset(yes=yes, as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


@local_app.command("status")
def local_status(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Check status of local PostgreSQL Docker container."""
    code = run_local_status(as_json=json_output)
    if code != 0:
        raise typer.Exit(code)


if __name__ == "__main__":
    app()
