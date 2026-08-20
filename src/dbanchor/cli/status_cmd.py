"""CLI command for dbx status."""

from __future__ import annotations

from typing import Optional
import typer
from rich.panel import Panel
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json


def run_status(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Show an instant high-level status card of the database and migrations."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    provider = db.get_provider()
    mig_state = db.get_migration_status()

    # Ping test
    conn_ok, latency, _ = False, 0.0, None
    if db.connector:
        conn_ok, latency, _ = db.connector.test_sync_connection()

    table_count = 0
    if conn_ok:
        try:
            snap = db.inspect_schema()
            table_count = len(snap.tables)
        except Exception:
            pass

    if as_json:
        data = {
            "provider": provider.name,
            "environment": config.environment.value,
            "connected": conn_ok,
            "latency_ms": latency,
            "host": db.conn_info.host if db.conn_info else None,
            "database": db.conn_info.database if db.conn_info else None,
            "tables_count": table_count,
            "migration_up_to_date": mig_state.is_up_to_date,
            "current_revision": mig_state.current_db_revision,
            "pending_migrations": mig_state.pending_count,
        }
        typer.echo(to_json(data))
        return 0 if conn_ok else 1

    console.print()
    console.rule("[bold cyan]Database Status Overview[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Sep", style="dim")
    table.add_column("Value")

    table.add_row("Provider", ":", f"[bold cyan]{provider.name}[/bold cyan]")
    table.add_row("Environment", ":", f"[{'red' if config.environment.is_production_like else 'green'}]{config.environment.value.upper()}[/]")
    if db.conn_info:
        table.add_row("Host", ":", db.conn_info.host or "-")
        table.add_row("Database", ":", db.conn_info.database or "-")

    table.add_row("Connection", ":", "[bold green][+] Connected[/bold green]" if conn_ok else "[bold red][x] Disconnected[/bold red]")
    table.add_row("Live Tables", ":", str(table_count))

    if mig_state.is_alembic_configured:
        mig_status_str = "[bold green][+] Up to date[/bold green]" if mig_state.is_up_to_date else f"[bold yellow][!]  {mig_state.pending_count} pending[/bold yellow]"
        table.add_row("Migration State", ":", mig_status_str)
        if mig_state.current_db_revision:
            table.add_row("Current Revision", ":", mig_state.current_db_revision)
    else:
        table.add_row("Migration State", ":", "[dim]Not configured[/dim]")

    panel = Panel(table, title="[bold]System Status[/bold]", border_style="cyan", expand=False)
    console.print(panel)
    console.print()
    return 0 if conn_ok else 1
