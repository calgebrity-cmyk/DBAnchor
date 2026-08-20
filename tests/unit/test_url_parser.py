"""Unit tests for URL parser, normalizer, and password encoding diagnostics."""

import pytest
from dbanchor.connection.url import (
    check_password_encoding_issues,
    parse_connection_url,
    to_async_url,
)


def test_parse_standard_postgresql_url():
    url = "postgresql://user:pass123@localhost:5432/mydb"
    info = parse_connection_url(url)
    assert info.scheme == "postgresql"
    assert info.username == "user"
    assert info.host == "localhost"
    assert info.port == 5432
    assert info.database == "mydb"
    assert info.driver == "default"
    assert info.is_localhost is True
    assert "pass123" not in info.safe_url
    assert "********" in info.safe_url


def test_normalize_legacy_postgres_scheme():
    url = "postgres://admin:secret@db.example.com:5433/production_db"
    info = parse_connection_url(url)
    assert info.normalized_url.startswith("postgresql://")
    assert info.port == 5433
    assert info.database == "production_db"


def test_parse_psycopg3_and_asyncpg_drivers():
    url_psycopg = "postgresql+psycopg://user:pass@localhost:5432/test"
    info_p = parse_connection_url(url_psycopg)
    assert info_p.driver == "psycopg"
    assert info_p.is_async is False

    url_async = "postgresql+asyncpg://user:pass@localhost:5432/test"
    info_a = parse_connection_url(url_async)
    assert info_a.driver == "asyncpg"
    assert info_a.is_async is True


def test_to_async_url():
    info = parse_connection_url("postgresql://user:pass@localhost:5432/mydb")
    async_url = to_async_url(info)
    assert async_url.startswith("postgresql+asyncpg://")


def test_unencoded_special_characters_in_password():
    raw_url = "postgresql://user:p@ssword#1@localhost:5432/mydb"
    has_warn, msg = check_password_encoding_issues(raw_url)
    assert has_warn is True
    assert msg is not None
    assert "URL-encoded" in msg or "multiple '@'" in msg or "unencoded '#'" in msg

    info = parse_connection_url(raw_url)
    assert info.has_encoding_warning is True


def test_empty_or_invalid_url():
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_connection_url("")

    with pytest.raises(ValueError, match="Unsupported database scheme"):
        parse_connection_url("mysql://user:pass@localhost/db")
