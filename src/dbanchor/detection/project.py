"""Project inspection and structure detection for DBAnchor."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ProjectDetectionResult(BaseModel):
    """Detected environment, framework, and tooling within the target directory."""
    project_root: str
    has_python: bool = True
    has_env_file: bool = False
    has_docker: bool = False
    has_docker_compose: bool = False
    has_pyproject: bool = False
    has_requirements: bool = False
    framework: Optional[str] = None
    orm: Optional[str] = None
    migration_tool: Optional[str] = None
    migration_dir: Optional[str] = None
    installed_drivers: list[str] = Field(default_factory=list)


def inspect_project_files(root_dir: str | Path | None = None) -> ProjectDetectionResult:
    """Inspect local project directory to detect Python frameworks, ORMs, and migration files."""
    root = Path(root_dir or Path.cwd()).resolve()

    has_env = (root / ".env").is_file() or (root / ".env.local").is_file()
    has_docker = (root / "Dockerfile").is_file()
    has_compose = (
        (root / "docker-compose.yml").is_file()
        or (root / "docker-compose.yaml").is_file()
        or (root / "compose.yml").is_file()
        or (root / "compose.yaml").is_file()
    )
    has_pyproject = (root / "pyproject.toml").is_file()
    has_reqs = (root / "requirements.txt").is_file()

    # Search for files/content hints
    content_samples: list[str] = []
    for candidate in [root / "pyproject.toml", root / "requirements.txt", root / "Pipfile"]:
        if candidate.is_file():
            try:
                content_samples.append(candidate.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                pass

    combined_deps = "\n".join(content_samples).lower()

    # Framework detection
    framework: Optional[str] = None
    if "fastapi" in combined_deps or (root / "main.py").is_file() and "FastAPI" in (root / "main.py").read_text(errors="ignore"):
        framework = "FastAPI"
    elif "django" in combined_deps or (root / "manage.py").is_file():
        framework = "Django"
    elif "flask" in combined_deps:
        framework = "Flask"
    elif "litestar" in combined_deps:
        framework = "Litestar"

    # ORM detection
    orm: Optional[str] = None
    if "sqlalchemy" in combined_deps:
        orm = "SQLAlchemy"
    elif "sqlmodel" in combined_deps:
        orm = "SQLModel"
    elif "tortoise-orm" in combined_deps or "tortoise" in combined_deps:
        orm = "Tortoise ORM"
    elif framework == "Django":
        orm = "Django ORM"

    # Migration system detection
    migration_tool: Optional[str] = None
    migration_dir: Optional[str] = None

    if (root / "alembic.ini").is_file() or (root / "migrations" / "env.py").is_file() or (root / "alembic" / "env.py").is_file():
        migration_tool = "Alembic"
        if (root / "alembic").is_dir():
            migration_dir = str(root / "alembic")
        elif (root / "migrations").is_dir():
            migration_dir = str(root / "migrations")
    elif framework == "Django":
        migration_tool = "Django Migrations"

    # Drivers
    drivers: list[str] = []
    for drv in ["psycopg", "psycopg2", "asyncpg"]:
        if drv in combined_deps:
            drivers.append(drv)

    return ProjectDetectionResult(
        project_root=str(root),
        has_python=True,
        has_env_file=has_env,
        has_docker=has_docker,
        has_docker_compose=has_compose,
        has_pyproject=has_pyproject,
        has_requirements=has_reqs,
        framework=framework,
        orm=orm,
        migration_tool=migration_tool,
        migration_dir=migration_dir,
        installed_drivers=drivers,
    )
