"""CLI command for dbx adopt."""

from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.migrations.adopt import plan_adoption
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json


def run_adopt(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    yes: bool = False,
    as_json: bool = False,
) -> int:
    """Adopt an existing database without modifying or deleting data."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    if not db.connector:
        console.print("[bold red]DATABASE_URL is not configured.[/bold red]\n")
        return 1

    plan = plan_adoption(db.connector)

    if as_json:
        if not yes:
            typer.echo(to_json(plan))
            return 0
        res = db.adopt()
        typer.echo(to_json(res))
        return 0 if res.success else 1

    console.print()
    console.rule("[bold cyan]DBAnchor Existing Project Adoption[/bold cyan]")
    console.print()

    console.print(f"[bold green]Existing Database Detected:[/bold green] {plan.table_count} tables found.")
    if plan.tables:
        console.print(f"  [dim]Tables: {', '.join(plan.tables[:10])}{'...' if len(plan.tables) > 10 else ''}[/dim]\n")

    console.print("[bold]Adoption Plan Steps:[/bold]")
    for step in plan.steps:
        console.print(f"  {step}")
    console.print()

    if not yes:
        confirm = typer.confirm("Proceed with adoption?")
        if not confirm:
            console.print("[yellow]Adoption cancelled.[/yellow]\n")
            return 0

    res = db.adopt()
    if res.success:
        console.print(f"[bold green][+] {res.message}[/bold green]\n")
        return 0
    else:
        console.print(f"[bold red][x] {res.message}[/bold red]\n")
        return 1
