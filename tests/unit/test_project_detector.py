"""Unit tests for project and framework inspection."""

from pathlib import Path
from dbanchor.detection.project import inspect_project_files


def test_inspect_empty_directory(tmp_path: Path):
    res = inspect_project_files(tmp_path)
    assert res.has_python is True
    assert res.has_env_file is False
    assert res.has_docker is False
    assert res.framework is None


def test_inspect_fastapi_project(tmp_path: Path):
    (tmp_path / ".env").write_text("DATABASE_URL=postgresql://localhost/db")
    (tmp_path / "pyproject.toml").write_text("[project]\ndependencies = ['fastapi', 'sqlalchemy', 'alembic', 'psycopg']")
    (tmp_path / "docker-compose.yml").write_text("version: '3'")

    res = inspect_project_files(tmp_path)
    assert res.has_env_file is True
    assert res.has_docker_compose is True
    assert res.framework == "FastAPI"
    assert res.orm == "SQLAlchemy"
    assert "psycopg" in res.installed_drivers
