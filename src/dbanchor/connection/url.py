"""Connection URL parsing, validation, normalization, and diagnostics."""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Optional
from dbanchor.output.redaction import redact_url

RESERVED_URL_CHARS = {"@", ":", "/", "?", "#", "[", "]", "%"}


@dataclass
class ConnectionInfo:
    """Structured, sanitized database connection details."""
    raw_url: str
    normalized_url: str
    scheme: str
    driver: str
    username: Optional[str] = None
    host: Optional[str] = None
    port: int = 5432
    database: Optional[str] = None
    query_params: dict[str, str] = field(default_factory=dict)
    ssl_mode: Optional[str] = None
    is_async: bool = False
    has_encoding_warning: bool = False
    encoding_warning_message: Optional[str] = None

    @property
    def safe_url(self) -> str:
        """Return the URL with password safely redacted."""
        return redact_url(self.normalized_url)

    @property
    def is_postgres(self) -> bool:
        return self.scheme.startswith("postgres")

    @property
    def is_localhost(self) -> bool:
        if not self.host:
            return False
        return self.host.lower() in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}

    def __repr__(self) -> str:
        return f"ConnectionInfo(scheme='{self.scheme}', driver='{self.driver}', host='{self.host}', port={self.port}, database='{self.database}', safe_url='{self.safe_url}')"


def check_password_encoding_issues(raw_url: str) -> tuple[bool, Optional[str]]:
    """Detect if a raw URL contains unencoded special characters in credentials."""
    if not raw_url or "://" not in raw_url:
        return False, None

    scheme_part, remainder = raw_url.split("://", 1)

    # If there are multiple '@' symbols before the path
    at_count = remainder.count("@")
    if at_count > 1:
        return True, (
            "The DATABASE_URL contains multiple '@' characters. "
            "If your database password contains '@' or other special characters, "
            "they must be URL-encoded (e.g. '@' -> '%40')."
        )

    # Check for unencoded '#' or '?' before '@'
    if "@" in remainder:
        cred_part, _ = remainder.split("@", 1)
        if "#" in cred_part:
            return True, (
                "The DATABASE_URL contains an unencoded '#' in credentials. "
                "URL fragment markers must be encoded as '%23'."
            )
        if "?" in cred_part:
            return True, (
                "The DATABASE_URL contains an unencoded '?' in credentials. "
                "Query parameter delimiters must be encoded as '%3F'."
            )

    return False, None


def parse_connection_url(url: str | None) -> ConnectionInfo:
    """Parse and normalize a PostgreSQL connection URL into structured ConnectionInfo.

    Handles postgres://, postgresql://, postgresql+psycopg://, postgresql+psycopg2://, postgresql+asyncpg://
    """
    if not url or not url.strip():
        raise ValueError("DATABASE_URL cannot be empty.")

    raw_url = url.strip()
    has_warn, warn_msg = check_password_encoding_issues(raw_url)

    # Normalize legacy postgres:// to postgresql://
    normalized = raw_url
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]

    try:
        parsed = urllib.parse.urlparse(normalized)
    except Exception as e:
        raise ValueError(f"Invalid DATABASE_URL format: {e}") from e

    scheme = parsed.scheme.lower()
    if not (scheme.startswith("postgres") or scheme.startswith("postgresql")):
        raise ValueError(
            f"Unsupported database scheme '{scheme}'. DBAnchor currently supports PostgreSQL."
        )

    # Determine driver and async capability
    driver = "default"
    is_async = False
    if "+" in scheme:
        _, driver = scheme.split("+", 1)
        if "async" in driver:
            is_async = True

    username = urllib.parse.unquote(parsed.username) if parsed.username else None
    host = parsed.hostname
    port = parsed.port or 5432
    database = parsed.path.lstrip("/") if parsed.path else None

    # Parse query parameters
    query_params: dict[str, str] = {}
    if parsed.query:
        query_dict = urllib.parse.parse_qs(parsed.query)
        query_params = {k: v[0] for k, v in query_dict.items() if v}

    ssl_mode = query_params.get("sslmode") or query_params.get("ssl")

    return ConnectionInfo(
        raw_url=raw_url,
        normalized_url=normalized,
        scheme=scheme,
        driver=driver,
        username=username,
        host=host,
        port=port,
        database=database,
        query_params=query_params,
        ssl_mode=ssl_mode,
        is_async=is_async,
        has_encoding_warning=has_warn,
        encoding_warning_message=warn_msg,
    )


def to_async_url(conn_info: ConnectionInfo) -> str:
    """Convert a connection URL to asyncpg dialect if not already async."""
    url = conn_info.normalized_url
    if "+asyncpg" in url or "+psycopg_async" in url:
        return url

    if "postgresql+psycopg://" in url:
        return url.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    if "postgresql+psycopg2://" in url:
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url
