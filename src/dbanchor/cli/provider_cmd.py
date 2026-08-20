"""CLI command for dbx provider detect."""

from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json


def run_provider_detect(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Detect database hosting provider from connection hostname patterns."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)
    provider = db.get_provider()

    if as_json:
        typer.echo(to_json(provider))
        return 0

    console.print()
    console.rule("[bold cyan]Database Provider Detection[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Sep", style="dim")
    table.add_column("Value")

    table.add_row("Detected Provider", ":", f"[bold cyan]{provider.name}[/bold cyan]")
    table.add_row("Type", ":", provider.provider_type.value)
    table.add_row("Serverless Auto-suspend", ":", "Yes" if provider.is_serverless else "No")
    table.add_row("SSL Enforced", ":", "[bold yellow]YES[/bold yellow]" if provider.requires_ssl else "Optional")
    table.add_row("Connection Pooler", ":", "Yes (PgBouncer/Supavisor)" if provider.is_connection_pooled else "Direct Port")

    console.print(table)
    console.print()

    if provider.recommendations:
        console.print("[bold]Provider Recommendations:[/bold]")
        for rec in provider.recommendations:
            console.print(f"  * {rec}")
        console.print()

    return 0
