"""Project, framework, and tooling detection for DBAnchor."""

from dbanchor.detection.framework import (
    is_alembic_available,
    is_django_available,
    is_fastapi_available,
    is_sqlalchemy_available,
)
from dbanchor.detection.project import ProjectDetectionResult, inspect_project_files

__all__ = [
    "ProjectDetectionResult",
    "inspect_project_files",
    "is_sqlalchemy_available",
    "is_alembic_available",
    "is_fastapi_available",
    "is_django_available",
]
