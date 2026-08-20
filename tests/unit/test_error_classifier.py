"""Unit tests for deterministic error classification."""

from dbanchor.diagnostics.classifier import classify_exception
from dbanchor.diagnostics.rules import DIAGNOSTIC_RULES


def test_classify_auth_failure():
    rule = classify_exception("password authentication failed for user 'postgres'")
    assert rule.code == "AUTH_FAILED"
    assert "28P01" in rule.title or "Authentication" in rule.title
    assert "No database changes" in rule.risk


def test_classify_database_not_found():
    rule = classify_exception('FATAL: database "my_missing_db" does not exist')
    assert rule.code == "DATABASE_NOT_FOUND"


def test_classify_connection_refused():
    rule = classify_exception("could not connect to server: Connection refused (0x0000274D/10061)")
    assert rule.code == "CONNECTION_REFUSED"
    assert "dbx local start" in (rule.safe_command or "")


def test_classify_alembic_multiple_heads():
    rule = classify_exception("Multiple heads are present; please use the 'heads' command")
    assert rule.code == "ALEMBIC_MULTIPLE_HEADS"
    assert "alembic merge heads" in rule.recommended_fix


def test_classify_alembic_revision_not_found():
    rule = classify_exception("Can't locate revision identified by 'a1b2c3d4'")
    assert rule.code == "ALEMBIC_REVISION_NOT_FOUND"


def test_classify_unencoded_special_characters():
    rule = classify_exception("authentication failed", context={"has_encoding_warning": True})
    assert rule.code == "UNENCODED_PASSWORD_SPECIAL_CHARS"
