"""CLI command for dbx config check."""

from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json


def run_config_check(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Validate configuration syntax, environment detection, and connection URL encoding."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    has_warn = db.conn_info.has_encoding_warning if db.conn_info else False
    warn_msg = db.conn_info.encoding_warning_message if db.conn_info else None

    if as_json:
        result = {
            "environment": config.environment.value,
            "has_url": bool(config.connection.url),
            "safe_url": db.safe_url,
            "connect_timeout": config.connection.connect_timeout,
            "pool_size": config.connection.pool_size,
            "has_encoding_warning": has_warn,
            "encoding_warning_message": warn_msg,
        }
        typer.echo(to_json(result))
        return 0 if not has_warn else 1

    console.print()
    console.rule("[bold cyan]DBAnchor Configuration Check[/bold cyan]")
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Sep", style="dim")
    table.add_column("Value")

    table.add_row("Environment", ":", f"[{'red' if config.environment.is_production_like else 'green'}]{config.environment.value.upper()}[/]")
    table.add_row("Configured URL", ":", f"[dim]{db.safe_url or '(None)'}[/dim]")
    table.add_row("Connect Timeout", ":", f"{config.connection.connect_timeout}s")
    table.add_row("Pool Size", ":", str(config.connection.pool_size))
    table.add_row("Auto-apply Dev", ":", str(config.migrations.auto_apply_dev))
    table.add_row("Allow Destructive", ":", f"[{'red' if config.safety.allow_destructive else 'green'}]{config.safety.allow_destructive}[/]")

    console.print(table)
    console.print()

    if has_warn and warn_msg:
        console.print(f"[bold yellow][!]  URL Warning: {warn_msg}[/bold yellow]\n")
        return 1

    console.print("[bold green][+] Configuration is valid.[/bold green]\n")
    return 0
