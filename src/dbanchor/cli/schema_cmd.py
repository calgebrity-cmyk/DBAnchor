"""CLI commands for dbx schema inspect and dbx schema diff."""

from __future__ import annotations

from typing import Optional
import typer
from rich.table import Table

from dbanchor.config.loader import load_config
from dbanchor.core.database import Database
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json
from dbanchor.schema.inspector import SchemaInspector
from dbanchor.schema.models import DriftReport, SchemaSnapshot


def run_schema_inspect(
    table_name: Optional[str] = None,
    schema: str = "public",
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Reflect and display live database tables, columns, indexes, and foreign keys."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    snapshot: SchemaSnapshot = db.inspect_schema(schema_name=schema)

    if as_json:
        typer.echo(to_json(snapshot))
        return 0

    console.print()
    console.rule("[bold cyan]Database Schema Inspection[/bold cyan]")
    console.print()

    if table_name:
        if table_name not in snapshot.tables:
            console.print(f"[bold red]Table '{table_name}' not found in schema '{schema}'.[/bold red]\n")
            return 1
        target_tables = {table_name: snapshot.tables[table_name]}
    else:
        target_tables = snapshot.tables

    if not target_tables:
        console.print(f"[yellow]No tables found in schema '{schema}'.[/yellow]\n")
        return 0

    for tname, tbl in target_tables.items():
        table = Table(title=f"Table: [bold cyan]{tname}[/bold cyan]", show_lines=True)
        table.add_column("Column", style="bold white")
        table.add_column("Data Type", style="cyan")
        table.add_column("Nullable", justify="center")
        table.add_column("Default", style="dim")
        table.add_column("Attributes", style="yellow")

        for col in tbl.columns.values():
            attrs = []
            if col.primary_key:
                attrs.append("PK")
            if col.unique:
                attrs.append("UNIQUE")

            null_str = "[green]YES[/green]" if col.nullable else "[red]NO[/red]"
            table.add_row(
                col.name,
                col.type_str,
                null_str,
                col.default or "-",
                ", ".join(attrs) if attrs else "-",
            )

        console.print(table)
        if tbl.indexes:
            idx_str = ", ".join(f"{i.name}({', '.join(i.columns)})" for i in tbl.indexes)
            console.print(f"  [dim]Indexes: {idx_str}[/dim]")
        if tbl.foreign_keys:
            fk_str = ", ".join(f"{','.join(f.constrained_columns)} -> {f.referred_table}({','.join(f.referred_columns)})" for f in tbl.foreign_keys)
            console.print(f"  [dim]Foreign Keys: {fk_str}[/dim]")
        console.print()

    return 0


def run_schema_diff(
    env_file: Optional[str] = None,
    url: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Compare application models against live database schema and detect schema drift."""
    config = load_config(env_file=env_file, url_override=url)
    db = Database(config=config)

    # Attempt to load target_metadata from alembic or application
    from dbanchor.migrations.state import find_alembic_config_path
    from dbanchor.schema.diff import compare_schemas

    live_snap = db.inspect_schema()

    # Try import models from env
    target_meta = None
    try:
        # Check if project has models module
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path.cwd()))
        for mod_name in ["app.models", "models", "src.models", "app.db"]:
            try:
                mod = __import__(mod_name, fromlist=["Base", "metadata"])
                if hasattr(mod, "Base") and hasattr(mod.Base, "metadata"):
                    target_meta = mod.Base.metadata
                    break
                elif hasattr(mod, "metadata"):
                    target_meta = mod.metadata
                    break
            except Exception:
                pass
    except Exception:
        pass

    if target_meta is None:
        if as_json:
            typer.echo(to_json({"status": "no_metadata", "message": "No SQLAlchemy Base.metadata discovered in current project."}))
            return 0
        console.print()
        console.rule("[bold cyan]Schema Drift Analysis[/bold cyan]")
        console.print("\n[yellow]Could not automatically discover application SQLAlchemy Base.metadata.[/yellow]")
        console.print("To run programmatic diff: [code]db.diff_schema(Base.metadata)[/code]\n")
        return 0

    drift: DriftReport = compare_schemas(target_meta, live_snap)

    if as_json:
        typer.echo(to_json(drift))
        return 0 if not drift.has_drift else 1

    console.print()
    console.rule("[bold cyan]Schema Drift Analysis[/bold cyan]")
    console.print()

    if not drift.has_drift:
        console.print("[bold green][+] Zero schema drift detected.[/bold green] Application models perfectly match the live database.\n")
        return 0

    console.print(f"[bold yellow][!]  Schema Drift Detected: {drift.total_differences} differences found.[/bold yellow]\n")

    diff_table = Table(title="Drift Breakdown", show_lines=True)
    diff_table.add_column("Type", style="bold yellow")
    diff_table.add_column("Table", style="bold white")
    diff_table.add_column("Expected (Code)", style="green")
    diff_table.add_column("Actual (Database)", style="red")
    diff_table.add_column("Risk", style="yellow")

    for d in drift.differences:
        diff_table.add_row(d.drift_type.value, d.table_name, d.expected or "-", d.actual or "-", d.risk)

    console.print(diff_table)
    console.print()
    return 1
