"""Local Docker PostgreSQL lifecycle manager for DBAnchor."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

CONTAINER_NAME = "dbanchor-postgres"
DEFAULT_IMAGE = "postgres:17-alpine"


class LocalContainerStatus(BaseModel):
    """Status of local Docker PostgreSQL container."""
    docker_available: bool = False
    is_running: bool = False
    container_id: Optional[str] = None
    image: Optional[str] = None
    port: int = 5432
    database: str = "app_db"
    user: str = "postgres"
    connection_url: str = ""
    message: str = ""


def check_docker_available() -> bool:
    """Check if Docker CLI is installed and responsive."""
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3,
        )
        return res.returncode == 0
    except Exception:
        return False


def get_local_container_status() -> LocalContainerStatus:
    """Check status of DBAnchor local PostgreSQL container."""
    if not check_docker_available():
        return LocalContainerStatus(
            docker_available=False,
            is_running=False,
            message="Docker is not installed or Docker daemon is not running.",
        )

    try:
        res = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name={CONTAINER_NAME}", "--format", "{{.ID}}|{{.Status}}|{{.Image}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=4,
        )
        output = res.stdout.strip()
        if not output:
            return LocalContainerStatus(
                docker_available=True,
                is_running=False,
                message=f"No container named '{CONTAINER_NAME}' found.",
            )

        parts = output.split("|")
        cid = parts[0]
        status_str = parts[1] if len(parts) > 1 else ""
        image = parts[2] if len(parts) > 2 else DEFAULT_IMAGE
        is_running = "Up" in status_str

        return LocalContainerStatus(
            docker_available=True,
            is_running=is_running,
            container_id=cid,
            image=image,
            port=5432,
            database="app_db",
            user="postgres",
            connection_url="postgresql://postgres:postgres@localhost:5432/app_db",
            message=f"Container '{CONTAINER_NAME}' is {('running' if is_running else 'stopped')} ({status_str}).",
        )
    except Exception as e:
        return LocalContainerStatus(
            docker_available=True,
            is_running=False,
            message=f"Failed to query Docker: {e}",
        )


def start_local_postgres(
    port: int = 5432,
    db_name: str = "app_db",
    user: str = "postgres",
    password: str = "postgres",
    image: str = DEFAULT_IMAGE,
    write_env: bool = True,
) -> tuple[bool, str]:
    """Start local PostgreSQL in Docker container and optionally write to .env."""
    if not check_docker_available():
        return False, "Docker is not available. Please install and start Docker Desktop/daemon."

    # Check if container exists
    status = get_local_container_status()
    if status.is_running:
        return True, f"PostgreSQL is already running on localhost:{port}."

    if status.container_id:
        # Restart existing container
        subprocess.run(["docker", "start", CONTAINER_NAME], check=True)
    else:
        # Run new container
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            CONTAINER_NAME,
            "-p",
            f"{port}:5432",
            "-e",
            f"POSTGRES_DB={db_name}",
            "-e",
            f"POSTGRES_USER={user}",
            "-e",
            f"POSTGRES_PASSWORD={password}",
            image,
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return False, f"Failed to start Docker container: {res.stderr}"

    conn_url = f"postgresql://{user}:{password}@localhost:{port}/{db_name}"

    if write_env:
        env_file = Path(".env")
        if not env_file.exists():
            env_file.write_text(f"DATABASE_URL={conn_url}\nAPP_ENV=development\n", encoding="utf-8")
        else:
            content = env_file.read_text(encoding="utf-8")
            if "DATABASE_URL" not in content:
                with open(env_file, "a", encoding="utf-8") as f:
                    f.write(f"\nDATABASE_URL={conn_url}\n")

    return True, f"Started local PostgreSQL container '{CONTAINER_NAME}' on localhost:{port}."


def stop_local_postgres() -> tuple[bool, str]:
    """Stop local PostgreSQL container."""
    if not check_docker_available():
        return False, "Docker is not available."
    try:
        subprocess.run(["docker", "stop", CONTAINER_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True, f"Stopped container '{CONTAINER_NAME}'."
    except Exception as e:
        return False, f"Failed to stop container: {e}"


def reset_local_postgres(confirm: bool = False) -> tuple[bool, str]:
    """Remove and reset local PostgreSQL container. Requires confirmation."""
    if not confirm:
        return False, "Resetting local database requires explicit confirmation (confirm=True)."

    if not check_docker_available():
        return False, "Docker is not available."

    try:
        subprocess.run(["docker", "rm", "-f", CONTAINER_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True, f"Reset complete. Removed container '{CONTAINER_NAME}'."
    except Exception as e:
        return False, f"Failed to reset container: {e}"
