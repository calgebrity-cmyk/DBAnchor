"""Connection engine manager for sync and async database operations."""

from __future__ import annotations

import socket
import time
from typing import Any, Optional
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from dbanchor.config.models import ConnectionConfig
from dbanchor.connection.pool import build_engine_kwargs
from dbanchor.connection.url import ConnectionInfo, parse_connection_url, to_async_url


def test_tcp_connectivity(host: str, port: int = 5432, timeout: float = 3.0) -> tuple[bool, float, Optional[str]]:
    """Test raw TCP socket connectivity to PostgreSQL host/port.

    Returns:
        (is_successful, elapsed_ms, error_message)
    """
    start_time = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return True, elapsed_ms, None
    except socket.timeout:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, elapsed_ms, f"Connection timed out after {timeout:.1f}s"
    except socket.gaierror as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, elapsed_ms, f"DNS resolution failed for '{host}': {e}"
    except ConnectionRefusedError:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, elapsed_ms, f"Connection refused on {host}:{port} (port closed or database not running)"
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return False, elapsed_ms, str(e)
    finally:
        sock.close()


test_tcp_connectivity.__test__ = False


class DatabaseConnector:
    """Manages SQLAlchemy sync and async engines and sessions."""

    def __init__(self, config: ConnectionConfig, connection_info: ConnectionInfo) -> None:
        self.config = config
        self.connection_info = connection_info
        self._sync_engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_session_factory: Optional[sessionmaker[Session]] = None
        self._async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> DatabaseConnector:
        info = parse_connection_url(url)
        config = ConnectionConfig(url=url, **kwargs)
        return cls(config, info)

    def get_sync_engine(self) -> Engine:
        """Create or return cached sync SQLAlchemy Engine."""
        if self._sync_engine is None:
            engine_kwargs = build_engine_kwargs(self.config)
            self._sync_engine = create_engine(
                self.connection_info.normalized_url,
                **engine_kwargs,
            )
        return self._sync_engine

    def get_async_engine(self) -> AsyncEngine:
        """Create or return cached async SQLAlchemy AsyncEngine."""
        if self._async_engine is None:
            async_url = to_async_url(self.connection_info)
            engine_kwargs = build_engine_kwargs(self.config)
            self._async_engine = create_async_engine(
                async_url,
                **engine_kwargs,
            )
        return self._async_engine

    def get_session(self) -> Session:
        """Create a new sync Session."""
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                bind=self.get_sync_engine(),
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._sync_session_factory()

    def get_async_session(self) -> AsyncSession:
        """Create a new async Session."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.get_async_engine(),
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._async_session_factory()

    def test_sync_connection(self) -> tuple[bool, float, Optional[str]]:
        """Test active SQL connectivity via SELECT 1."""
        start_time = time.perf_counter()
        try:
            engine = self.get_sync_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return True, elapsed_ms, None
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return False, elapsed_ms, str(e)

    def close(self) -> None:
        """Dispose of underlying connection pools."""
        if self._sync_engine is not None:
            self._sync_engine.dispose()
            self._sync_engine = None
        if self._async_engine is not None:
            # Note: disposal of async engine is handled via sync wrapper or gc
            self._async_engine.sync_engine.dispose()
            self._async_engine = None
