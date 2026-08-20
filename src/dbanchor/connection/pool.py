"""Connection pool configuration and strategies for DBAnchor."""

from __future__ import annotations

from typing import Any
from dbanchor.config.models import ConnectionConfig


def build_engine_kwargs(config: ConnectionConfig) -> dict[str, Any]:
    """Build standardized SQLAlchemy engine arguments."""
    kwargs: dict[str, Any] = {
        "pool_pre_ping": config.pool_pre_ping,
        "pool_recycle": config.pool_recycle,
        "echo": config.echo,
    }

    # If using QueuePool (default for psycopg/psycopg2)
    if config.pool_size > 0:
        kwargs["pool_size"] = config.pool_size
        kwargs["max_overflow"] = config.max_overflow

    # Pass connect_timeout into connect_args
    connect_args: dict[str, Any] = {}
    if config.connect_timeout > 0:
        connect_args["connect_timeout"] = config.connect_timeout

    if connect_args:
        kwargs["connect_args"] = connect_args

    return kwargs
