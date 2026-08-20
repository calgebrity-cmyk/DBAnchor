"""CLI commands for dbx local subcommands."""

from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from dbanchor.local.docker_manager import (
    get_local_container_status,
    reset_local_postgres,
    start_local_postgres,
    stop_local_postgres,
)
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json


def run_local_start(
    port: int = 5432,
    database: str = "app_db",
    user: str = "postgres",
    password: str = "postgres",
    as_json: bool = False,
) -> int:
    """Start local Docker PostgreSQL container."""
    ok, msg = start_local_postgres(port=port, db_name=database, user=user, password=password)
    if as_json:
        typer.echo(to_json({"success": ok, "message": msg}))
        return 0 if ok else 1

    if ok:
        console.print(f"[bold green][+] {msg}[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red][x] {msg}[/bold red]\n")
        return 1


def run_local_stop(as_json: bool = False) -> int:
    """Stop local Docker PostgreSQL container."""
    ok, msg = stop_local_postgres()
    if as_json:
        typer.echo(to_json({"success": ok, "message": msg}))
        return 0 if ok else 1

    if ok:
        console.print(f"[bold green][+] {msg}[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red][x] {msg}[/bold red]\n")
        return 1


def run_local_reset(
    yes: bool = False,
    as_json: bool = False,
) -> int:
    """Reset and remove local Docker PostgreSQL container (requires confirmation)."""
    if not yes:
        confirm = typer.confirm("Are you sure you want to RESET the local database? All local data will be deleted.")
        if not confirm:
            console.print("[yellow]Reset cancelled.[/yellow]\n")
            return 0

    ok, msg = reset_local_postgres(confirm=True)
    if as_json:
        typer.echo(to_json({"success": ok, "message": msg}))
        return 0 if ok else 1

    if ok:
        console.print(f"[bold green][+] {msg}[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red][x] {msg}[/bold red]\n")
        return 1


def run_local_status(as_json: bool = False) -> int:
    """Check status of local Docker PostgreSQL container."""
    status = get_local_container_status()
    if as_json:
        typer.echo(to_json(status))
        return 0 if status.is_running else 1

    console.print()
    console.rule("[bold cyan]Local Docker PostgreSQL Status[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Sep", style="dim")
    table.add_column("Value")

    table.add_row("Docker Daemon", ":", "[green]Available[/green]" if status.docker_available else "[red]Not Available[/red]")
    table.add_row("Container Status", ":", "[bold green]Running[/bold green]" if status.is_running else "[yellow]Stopped[/yellow]")
    if status.container_id:
        table.add_row("Container ID", ":", status.container_id[:12])
        table.add_row("Image", ":", status.image or "-")
        table.add_row("Port", ":", f"localhost:{status.port}")
        table.add_row("Database", ":", status.database)

    console.print(table)
    console.print()
    return 0 if status.is_running else 1
