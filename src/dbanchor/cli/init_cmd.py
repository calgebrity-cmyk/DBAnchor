"""CLI command for dbx init."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import typer
from rich.panel import Panel
from rich.table import Table

from dbanchor.detection.project import inspect_project_files
from dbanchor.output.console import console
from dbanchor.output.json_formatter import to_json

SAMPLE_ENV_CONTENT = """# PostgreSQL Database Connection URL
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db

# Application Environment (development, test, staging, production)
APP_ENV=development
"""


def run_init(
    project_dir: Optional[str] = None,
    as_json: bool = False,
) -> int:
    """Inspect local project structure and configure DBAnchor."""
    root = Path(project_dir or Path.cwd()).resolve()
    detection = inspect_project_files(root)

    if as_json:
        typer.echo(to_json(detection))
        return 0

    console.print()
    console.rule("[bold cyan]DBAnchor Project Initialization[/bold cyan]")
    console.print()

    table = Table(title="[bold]Detected Project Components[/bold]", show_lines=False)
    table.add_column("Component", style="bold white", width=24)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    table.add_row("Python Project", "[bold green][+] DETECTED[/bold green]", str(root))
    table.add_row(".env File", "[bold green][+] FOUND[/bold green]" if detection.has_env_file else "[yellow]- MISSING[/yellow]", ".env" if detection.has_env_file else "Will generate template")
    table.add_row("Framework", f"[bold cyan]{detection.framework}[/bold cyan]" if detection.framework else "[dim]-[/dim]", detection.framework or "Standard Python")
    table.add_row("ORM", f"[bold cyan]{detection.orm}[/bold cyan]" if detection.orm else "[dim]-[/dim]", detection.orm or "Not detected")
    table.add_row("Migration System", f"[bold cyan]{detection.migration_tool}[/bold cyan]" if detection.migration_tool else "[yellow]- None[/yellow]", detection.migration_dir or "Run 'dbx adopt' to setup")
    table.add_row("Docker", "[bold green][+] FOUND[/bold green]" if (detection.has_docker or detection.has_docker_compose) else "[dim]-[/dim]", "docker-compose.yml" if detection.has_docker_compose else "Dockerfile" if detection.has_docker else "Not present")

    console.print(table)
    console.print()

    # Generate .env if missing
    env_path = root / ".env"
    if not env_path.is_file():
        env_path.write_text(SAMPLE_ENV_CONTENT, encoding="utf-8")
        console.print("[bold green][+] Created default .env configuration.[/bold green]")
        console.print("  [dim]Update DATABASE_URL with your PostgreSQL credentials.[/dim]\n")
    else:
        console.print("[bold green][+] Existing .env file detected.[/bold green]\n")

    console.print("[bold cyan]Next Steps:[/bold cyan]")
    console.print("  1. Verify connection: [code]dbx doctor[/code]")
    console.print("  2. If using Docker:    [code]dbx local start[/code]")
    console.print("  3. Run migrations:     [code]dbx migrate[/code]\n")

    return 0
