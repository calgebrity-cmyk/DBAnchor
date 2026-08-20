"""Rich console rendering and visual formatting for DBAnchor CLI."""

from __future__ import annotations

import json
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

# Custom brand theme
DBANCHOR_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "danger": "bold red",
        "success": "bold green",
        "muted": "dim",
        "highlight": "bold cyan",
        "brand": "bold blue",
        "code": "bold white on grey23",
    }
)

console = Console(theme=DBANCHOR_THEME, highlight=False)
error_console = Console(theme=DBANCHOR_THEME, stderr=True, highlight=False)


def print_banner() -> None:
    """Print the DBAnchor brand banner."""
    text = Text()
    text.append("DBAnchor", style="bold cyan")
    text.append(" -- Safe Database Middleware & Diagnostics", style="dim")
    console.print(text)
    console.print()


def print_status_card(
    title: str,
    fields: list[tuple[str, str, str]],  # (Label, Value, StatusColor)
    footer: str | None = None,
) -> None:
    """Print a clean key-value status card."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold white")
    table.add_column("Separator", style="dim")
    table.add_column("Value")

    for key, val, color in fields:
        table.add_row(key, ":", f"[{color}]{val}[/{color}]")

    content: Any = table
    if footer:
        content = Table.grid(padding=1)
        content.add_row(table)
        content.add_row(Text(footer, style="bold"))

    panel = Panel(
        table,
        title=f"[bold cyan] {title} [/bold cyan]",
        border_style="cyan",
        expand=False,
    )
    console.print(panel)


def print_diagnostic_box(
    title: str,
    what_happened: str,
    why_it_happened: str,
    risk: str,
    what_not_to_do: str | None = None,
    recommended_fix: str | None = None,
    safe_command: str | None = None,
    severity: str = "HIGH",
) -> None:
    """Print a senior-engineer style diagnostic box with root-cause and safe recommendations."""
    border_color = "red" if severity in {"HIGH", "CRITICAL"} else "yellow" if severity == "MEDIUM" else "cyan"

    content = Text()
    content.append("WHAT HAPPENED:\n", style="bold white")
    content.append(f"{what_happened}\n\n", style="white")

    content.append("LIKELY CAUSE:\n", style="bold white")
    content.append(f"{why_it_happened}\n\n", style="white")

    content.append("RISK LEVEL: ", style="bold white")
    risk_style = "bold red" if severity in {"HIGH", "CRITICAL"} else "bold yellow"
    content.append(f"{risk}\n\n", style=risk_style)

    if what_not_to_do:
        content.append("[!] WHAT NOT TO DO:\n", style="bold red")
        content.append(f"{what_not_to_do}\n\n", style="yellow")

    if recommended_fix:
        content.append("[*] RECOMMENDED ACTION:\n", style="bold green")
        content.append(f"{recommended_fix}\n", style="white")

    if safe_command:
        content.append("\nSAFE COMMAND:\n", style="bold cyan")
        content.append(f"  {safe_command}\n", style="bold white on grey23")

    panel = Panel(
        content,
        title=f"[{border_color}] {title} [/{border_color}]",
        border_style=border_color,
        expand=False,
        padding=(1, 2),
    )
    console.print(panel)
