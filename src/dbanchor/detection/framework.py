"""Framework and runtime ORM detection for DBAnchor."""

from __future__ import annotations

import sys
from typing import Optional


def is_sqlalchemy_available() -> bool:
    """Check if SQLAlchemy is installed in Python environment."""
    return "sqlalchemy" in sys.modules or _can_import("sqlalchemy")


def is_alembic_available() -> bool:
    """Check if Alembic is installed in Python environment."""
    return "alembic" in sys.modules or _can_import("alembic")


def is_fastapi_available() -> bool:
    """Check if FastAPI is installed in Python environment."""
    return "fastapi" in sys.modules or _can_import("fastapi")


def is_django_available() -> bool:
    """Check if Django is installed in Python environment."""
    return "django" in sys.modules or _can_import("django")


def _can_import(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except (ImportError, Exception):
        return False
