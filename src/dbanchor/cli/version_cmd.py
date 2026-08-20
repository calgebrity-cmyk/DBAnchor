"""CLI command for dbx version."""

from __future__ import annotations

import sys
import typer
from rich.table import Table

from dbanchor.detection.framework import (
    is_alembic_available,
    is_django_available,
    is_fastapi_available,
    is_sqlalchemy_available,
)
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json

VERSION = "0.1.0"


def run_version(as_json: bool = False) -> int:
    """Display DBAnchor version and installed driver capabilities."""
    caps = {
        "version": VERSION,
        "python": sys.version.split()[0],
        "sqlalchemy": is_sqlalchemy_available(),
        "alembic": is_alembic_available(),
        "fastapi": is_fastapi_available(),
        "django": is_django_available(),
    }

    if as_json:
        typer.echo(to_json(caps))
        return 0

    console.print()
    console.print(f"[bold cyan]DBAnchor[/bold cyan] version [bold white]{VERSION}[/bold white]")
    console.print(f"[dim]Python {sys.version.split()[0]}[/dim]\n")

    table = Table(title="Installed Ecosystem Capabilities", show_lines=False)
    table.add_column("Ecosystem Tool", style="bold white")
    table.add_column("Status")

    table.add_row("SQLAlchemy", "[bold green][+] Available[/bold green]" if caps["sqlalchemy"] else "[dim]Not installed[/dim]")
    table.add_row("Alembic", "[bold green][+] Available[/bold green]" if caps["alembic"] else "[dim]Not installed[/dim]")
    table.add_row("FastAPI", "[bold green][+] Available[/bold green]" if caps["fastapi"] else "[dim]Not installed[/dim]")
    table.add_row("Django", "[bold green][+] Available[/bold green]" if caps["django"] else "[dim]Not installed[/dim]")

    console.print(table)
    console.print()
    return 0
