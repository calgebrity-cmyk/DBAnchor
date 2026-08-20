"""CLI command for dbx connect."""

from __future__ import annotations

import time
from typing import Optional
import typer
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.connection.connector import DatabaseConnector
from dbanchor.core.database import Database
from dbanchor.output.console import console, print_diagnostic_box
from dbanchor.output.json_formatter import to_json


def run_connect(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Test active database connectivity and display sanitized connection details."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    if not db.conn_info:
        if as_json:
            typer.echo(to_json({"status": "failed", "error": "DATABASE_URL is not set."}))
            return 1
        console.print("[bold red]DATABASE_URL is not configured in .env or environment.[/bold red]\n")
        return 1

    provider = db.get_provider()

    # Test connection
    start = time.perf_counter()
    ok, latency_ms, err = False, 0.0, None
    if db.connector:
        ok, latency_ms, err = db.connector.test_sync_connection()

    if as_json:
        result = {
            "success": ok,
            "latency_ms": latency_ms,
            "host": db.conn_info.host,
            "port": db.conn_info.port,
            "database": db.conn_info.database,
            "user": db.conn_info.username,
            "provider": provider.name,
            "safe_url": db.safe_url,
            "error": err,
        }
        typer.echo(to_json(result))
        return 0 if ok else 1

    console.print()
    console.rule("[bold cyan]Database Connection Verification[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Sep", style="dim")
    table.add_column("Value")

    table.add_row("Provider", ":", f"[bold cyan]{provider.name}[/bold cyan]")
    table.add_row("Host", ":", db.conn_info.host or "-")
    table.add_row("Port", ":", str(db.conn_info.port))
    table.add_row("Database", ":", db.conn_info.database or "-")
    table.add_row("Username", ":", db.conn_info.username or "-")
    table.add_row("Safe URL", ":", f"[dim]{db.safe_url}[/dim]")

    if ok:
        table.add_row("Ping Status", ":", f"[bold green][+] SUCCESS[/bold green] ({latency_ms:.1f} ms)")
    else:
        table.add_row("Ping Status", ":", f"[bold red][x] FAILED[/bold red] ({latency_ms:.1f} ms)")

    console.print(table)
    console.print()

    if not ok and err:
        diag = db.diagnose(err)
        print_diagnostic_box(
            title=diag.title,
            what_happened=diag.what_happened,
            why_it_happened=diag.why_it_happened,
            risk=diag.risk,
            what_not_to_do=diag.what_not_to_do,
            recommended_fix=diag.recommended_fix,
            safe_command=diag.safe_command,
            severity=diag.severity,
        )
        console.print()
        return 1

    console.print("[bold green]Connection established successfully.[/bold green]\n")
    return 0
