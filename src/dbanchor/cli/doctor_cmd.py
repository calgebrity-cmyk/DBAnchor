"""CLI command for dbx doctor."""

from __future__ import annotations

import sys
from typing import Optional
import typer
from rich.panel import Panel
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.health.models import CheckStatus, HealthReport, OverallHealthStatus
from dbanchor.output.console import console, print_diagnostic_box
from dbanchor.output.json_formatter import to_json


def run_doctor(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
    verbose: bool = False,
) -> int:
    """Run database diagnostics and health checks."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    report: HealthReport = db.check_health()

    if as_json:
        typer.echo(to_json(report))
        return 0 if report.is_healthy else 1

    # Human-readable visual output
    console.print()
    console.rule("[bold cyan]DBAnchor Database Doctor[/bold cyan]")
    console.print()

    # Overview Table
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("Key", style="bold white")
    summary_table.add_column("Sep", style="dim")
    summary_table.add_column("Value")

    summary_table.add_row("Provider", ":", f"[bold cyan]{report.provider.name}[/bold cyan]")
    summary_table.add_row(
        "Environment",
        ":",
        f"[{'red' if report.environment.is_production_like else 'green'}]{report.environment.value.upper()}[/]",
    )
    if report.postgres_version:
        summary_table.add_row("Database Engine", ":", report.postgres_version)
    if report.host:
        summary_table.add_row("Host", ":", report.host)
    if report.database_name:
        summary_table.add_row("Target DB", ":", report.database_name)
    if report.active_user:
        summary_table.add_row("Active User", ":", report.active_user)

    status_color = "bold green" if report.status == OverallHealthStatus.READY else "bold yellow" if report.status == OverallHealthStatus.DEGRADED else "bold red"
    summary_table.add_row("Health Status", ":", f"[{status_color}]{report.status.value}[/{status_color}]")

    panel = Panel(summary_table, title="[bold]Summary[/bold]", border_style="cyan", expand=False)
    console.print(panel)
    console.print()

    # Checks Table
    checks_table = Table(title="[bold]Subsystem Health Checks[/bold]", show_lines=False, expand=False)
    checks_table.add_column("Status", justify="center", width=8)
    checks_table.add_column("Subsystem", style="bold white", width=28)
    checks_table.add_column("Message", style="white")
    checks_table.add_column("Latency", justify="right", style="dim", width=12)

    for c in report.checks:
        icon_str = f"[{c.status.color}]{c.status.icon} {c.status.value}[/{c.status.color}]"
        lat_str = f"{c.elapsed_ms:.1f} ms" if c.elapsed_ms > 0 else "-"
        checks_table.add_row(icon_str, c.name, c.message, lat_str)

    console.print(checks_table)
    console.print()

    # If any check has a diagnostic explanation, print it prominently
    for c in report.checks:
        if c.diagnostic:
            print_diagnostic_box(
                title=f"Diagnostic: {c.diagnostic.title}",
                what_happened=c.diagnostic.what_happened,
                why_it_happened=c.diagnostic.why_it_happened,
                risk=c.diagnostic.risk,
                what_not_to_do=c.diagnostic.what_not_to_do,
                recommended_fix=c.diagnostic.recommended_fix,
                safe_command=c.diagnostic.safe_command,
                severity=c.diagnostic.severity,
            )
            console.print()

    # Provider recommendations if available
    if report.provider.recommendations and verbose:
        console.print("[bold cyan]Provider Recommendations:[/bold cyan]")
        for rec in report.provider.recommendations:
            console.print(f"  * [dim]{rec}[/dim]")
        console.print()

    console.rule(f"[{status_color}]Status: {report.status.value}[/{status_color}]")
    console.print()

    return 0 if report.status in {OverallHealthStatus.READY, OverallHealthStatus.DEGRADED} else 1
