"""Integration tests for local Docker container manager."""

from dbanchor.local.docker_manager import (
    check_docker_available,
    get_local_container_status,
    reset_local_postgres,
)


def test_docker_available_check():
    # Calling check_docker_available() should return a bool without raising
    res = check_docker_available()
    assert isinstance(res, bool)


def test_get_local_container_status():
    status = get_local_container_status()
    assert hasattr(status, "docker_available")
    assert hasattr(status, "is_running")


def test_reset_local_postgres_requires_confirmation():
    ok, msg = reset_local_postgres(confirm=False)
    assert ok is False
    assert "confirmation" in msg
