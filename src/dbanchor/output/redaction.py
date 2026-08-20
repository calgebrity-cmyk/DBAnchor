"""Secret and credential redaction utilities for DBAnchor."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

# Common credential patterns in URLs and strings
PASSWORD_URL_PATTERN = re.compile(r"(://[^:]+:)([^@]+)(@)", re.IGNORECASE)
KEY_VALUE_PASSWORD_PATTERN = re.compile(
    r"(password|pwd|secret|token|api_key|access_token)\s*=\s*['\"]?([^'\"\s&]+)['\"]?",
    re.IGNORECASE,
)


def redact_url(url: str | None) -> str:
    """Redact passwords from connection URLs safely.

    Example:
        postgresql://user:secret123@localhost:5432/mydb ->
        postgresql://user:********@localhost:5432/mydb
    """
    if not url:
        return ""

    try:
        parsed = urlparse(url)
        if parsed.password:
            # Build redacted netloc
            user = parsed.username or ""
            host = parsed.hostname or ""
            port = f":{parsed.port}" if parsed.port else ""

            netloc = f"{user}:********@{host}{port}" if user else f"********@{host}{port}"
            redacted_parts = list(parsed)
            redacted_parts[1] = netloc
            return urlunparse(redacted_parts)
    except Exception:
        pass

    # Fallback to regex replacement
    return PASSWORD_URL_PATTERN.sub(r"\1********\3", url)


def redact_secrets(text: str) -> str:
    """Redact passwords and secret tokens from arbitrary strings or error messages."""
    if not text:
        return ""
    # Redact URL passwords
    redacted = PASSWORD_URL_PATTERN.sub(r"\1********\3", text)
    # Redact key=value passwords
    redacted = KEY_VALUE_PASSWORD_PATTERN.sub(r"\1=********", redacted)
    return redacted


def sanitize_data_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize sensitive values in dictionaries."""
    sanitized: dict[str, Any] = {}
    sensitive_keys = {
        "password",
        "pwd",
        "secret",
        "token",
        "api_key",
        "access_token",
        "database_url",
        "url",
        "connection_string",
    }

    for key, value in data.items():
        lower_key = str(key).lower()
        if isinstance(value, dict):
            sanitized[key] = sanitize_data_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_data_dict(item) if isinstance(item, dict)
                else redact_url(str(item)) if any(s in lower_key for s in ["url", "connection"])
                else item
                for item in value
            ]
        elif lower_key in {"database_url", "url", "connection_string", "dsn"}:
            sanitized[key] = redact_url(str(value)) if value else value
        elif any(s in lower_key for s in ["password", "pwd", "secret", "token", "key"]):
            sanitized[key] = "********" if value else value
        elif isinstance(value, str):
            sanitized[key] = redact_secrets(value)
        else:
            sanitized[key] = value

    return sanitized
