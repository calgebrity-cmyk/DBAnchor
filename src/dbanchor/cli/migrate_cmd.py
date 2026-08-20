"""CLI commands for dbx migrate and dbx migration subcommands."""

from __future__ import annotations

from typing import Optional
import typer
from rich.panel import Panel
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.diagnostics.engine import DiagnosticEngine
from dbanchor.output.console import console, print_diagnostic_box
from dbanchor.output.json_formatter import to_json
from dbanchor.safety.models import RiskLevel


def run_migrate(
    dry_run: bool = False,
    force_destructive: bool = False,
    yes: bool = False,
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Safely apply pending migrations to the database."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    # 1. Preview plan first
    plan = db.plan_migrations()

    if as_json:
        if dry_run:
            typer.echo(to_json(plan))
            return 0
        res = db.migrate(dry_run=dry_run, force_destructive=force_destructive)
        typer.echo(to_json(res))
        return 0 if res.success else 1

    console.print()
    console.rule("[bold cyan]DBAnchor Migration Engine[/bold cyan]")
    console.print()

    if not plan.pending_revisions:
        console.print("[bold green][+] Database is already up to date.[/bold green] No pending migrations.\n")
        return 0

    # Print plan table
    table = Table(title=f"Pending Migrations ({len(plan.pending_revisions)})", show_lines=True)
    table.add_column("Step", justify="center", width=6)
    table.add_column("Revision ID", style="bold cyan", width=16)
    table.add_column("Down Revision", style="dim", width=16)
    table.add_column("Description", style="white")

    for idx, rev in enumerate(plan.pending_revisions, 1):
        table.add_row(str(idx), rev.revision, rev.down_revision or "base", rev.message or "(no message)")

    console.print(table)
    console.print()

    # Safety Assessment
    risk_color = plan.safety_assessment.overall_risk.color
    console.print(f"Safety Risk Assessment: [{risk_color}]{plan.safety_assessment.overall_risk.value}[/{risk_color}]")

    if plan.safety_assessment.is_destructive:
        console.print("\n[bold red][!]  DESTRUCTIVE OPERATIONS DETECTED:[/bold red]")
        for op in plan.safety_assessment.operations:
            console.print(f"  * [{op.risk_level.color}][{op.risk_level.value}][/{op.risk_level.color}] {op.operation_type.value}: [bold white]{op.target_object}[/bold white]")
            console.print(f"    Reason: {op.reason}")
        console.print()

    if dry_run:
        console.print("[dim]Dry run complete. No database changes were made.[/dim]\n")
        return 0

    # Production safety confirmation
    if config.environment.is_production_like and plan.safety_assessment.is_destructive and not force_destructive:
        console.print("[bold red]Execution BLOCKED in production.[/bold red] Destructive changes require '--force-destructive' flag.\n")
        return 1

    if not yes and not config.environment.is_development_or_test:
        confirm = typer.confirm("Apply these migrations now?")
        if not confirm:
            console.print("[yellow]Migration cancelled by user.[/yellow]\n")
            return 0

    # Execute
    res = db.migrate(force_destructive=force_destructive)
    if res.success:
        console.print(f"\n[bold green][+] {res.message}[/bold green]\n")
        return 0
    else:
        console.print(f"\n[bold red][x] {res.message}[/bold red]\n")
        if res.diagnostic:
            print_diagnostic_box(
                title=res.diagnostic.title,
                what_happened=res.diagnostic.what_happened,
                why_it_happened=res.diagnostic.why_it_happened,
                risk=res.diagnostic.risk,
                what_not_to_do=res.diagnostic.what_not_to_do,
                recommended_fix=res.diagnostic.recommended_fix,
                safe_command=res.diagnostic.safe_command,
                severity=res.diagnostic.severity,
            )
            console.print()
        return 1


def run_migration_status(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Show detailed Alembic migration status and database revision."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)
    state = db.get_migration_status()

    if as_json:
        typer.echo(to_json(state))
        return 0 if state.is_up_to_date else 1

    console.print()
    console.rule("[bold cyan]Alembic Migration Status[/bold cyan]")
    console.print()

    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("Key", style="bold white")
    status_table.add_column("Sep", style="dim")
    status_table.add_column("Value")

    status_table.add_row("Current DB Revision", ":", state.current_db_revision or "(None / Unmigrated)")
    status_table.add_row("Codebase Head", ":", ", ".join(state.codebase_heads) or "(None)")
    status_table.add_row("Pending Migrations", ":", str(state.pending_count))

    status_color = "bold green" if state.is_up_to_date else "bold yellow" if not state.is_diverged else "bold red"
    status_label = "UP TO DATE" if state.is_up_to_date else "OUT OF DATE" if not state.is_diverged else "DIVERGED"
    status_table.add_row("Status", ":", f"[{status_color}]{status_label}[/{status_color}]")

    panel = Panel(status_table, title="[bold]Revision Overview[/bold]", border_style="cyan", expand=False)
    console.print(panel)
    console.print()

    if state.pending_revisions:
        table = Table(title="Pending Migrations", show_lines=False)
        table.add_column("Revision", style="bold cyan")
        table.add_column("Down Revision", style="dim")
        table.add_column("Message", style="white")
        for rev in state.pending_revisions:
            table.add_row(rev.revision, rev.down_revision or "base", rev.message or "(no doc)")
        console.print(table)
        console.print()

    return 0 if state.is_up_to_date else 1


def run_migration_explain(
    error_or_revision: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Explain a migration error or explain the current revision graph."""
    if not error_or_revision:
        error_or_revision = "migration failed"

    diag = DiagnosticEngine.diagnose_error(error_or_revision)
    if as_json:
        typer.echo(to_json(diag))
        return 0

    console.print()
    print_diagnostic_box(
        title=f"Explanation: {diag.title}",
        what_happened=diag.what_happened,
        why_it_happened=diag.why_it_happened,
        risk=diag.risk,
        what_not_to_do=diag.what_not_to_do,
        recommended_fix=diag.recommended_fix,
        safe_command=diag.safe_command,
        severity=diag.severity,
    )
    console.print()
    return 0
