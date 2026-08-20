"""Exception and error classification engine for PostgreSQL and Alembic."""

from __future__ import annotations

import socket
from typing import Any, Optional
from dbanchor.diagnostics.rules import DIAGNOSTIC_RULES, DiagnosticRule


def classify_exception(exc: Exception | str, context: Optional[dict[str, Any]] = None) -> DiagnosticRule:
    """Deterministically classify an exception or error message into a DiagnosticRule."""
    err_str = str(exc).lower()
    ctx = context or {}

    # 1. Check if special character unencoded password was flagged
    if ctx.get("has_encoding_warning") or "multiple '@'" in err_str:
        return DIAGNOSTIC_RULES["UNENCODED_PASSWORD_SPECIAL_CHARS"]

    # 2. Extract SQLSTATE code if available
    orig_exc = getattr(exc, "orig", None)
    pgcode = getattr(orig_exc, "pgcode", None) or getattr(orig_exc, "sqlstate", None)

    if pgcode:
        pgcode = str(pgcode).upper()
        if pgcode in {"28P01", "28000"}:
            return DIAGNOSTIC_RULES["AUTH_FAILED"]
        if pgcode == "3D000":
            return DIAGNOSTIC_RULES["DATABASE_NOT_FOUND"]
        if pgcode == "42P01":
            return DIAGNOSTIC_RULES["TABLE_NOT_FOUND"]
        if pgcode == "42703":
            return DIAGNOSTIC_RULES["COLUMN_NOT_FOUND"]
        if pgcode in {"42P07", "42701", "42710"}:
            return DIAGNOSTIC_RULES["DUPLICATE_OBJECT"]
        if pgcode == "42501":
            return DIAGNOSTIC_RULES["PERMISSION_DENIED"]

    # 3. Socket / Network errors
    if isinstance(exc, (socket.gaierror, ConnectionResetError)) or "getaddrinfo failed" in err_str or "name or service not known" in err_str:
        return DIAGNOSTIC_RULES["HOST_UNREACHABLE"]

    if isinstance(exc, (ConnectionRefusedError, socket.timeout)) or "connection refused" in err_str or "10061" in err_str or "could not connect to server" in err_str or "errno 111" in err_str:
        return DIAGNOSTIC_RULES["CONNECTION_REFUSED"]

    # 4. String pattern matching
    if "password authentication failed" in err_str or "auth failed" in err_str:
        return DIAGNOSTIC_RULES["AUTH_FAILED"]

    if "database" in err_str and "does not exist" in err_str:
        return DIAGNOSTIC_RULES["DATABASE_NOT_FOUND"]

    if "relation" in err_str and "does not exist" in err_str:
        return DIAGNOSTIC_RULES["TABLE_NOT_FOUND"]

    if "column" in err_str and "does not exist" in err_str:
        return DIAGNOSTIC_RULES["COLUMN_NOT_FOUND"]

    if "already exists" in err_str:
        return DIAGNOSTIC_RULES["DUPLICATE_OBJECT"]

    if "ssl" in err_str or "certificate" in err_str or "no pg_hba.conf entry" in err_str:
        return DIAGNOSTIC_RULES["SSL_REQUIRED_OR_FAILED"]

    if "permission denied" in err_str:
        return DIAGNOSTIC_RULES["PERMISSION_DENIED"]

    if "multiple heads" in err_str or "multiple head revisions" in err_str:
        return DIAGNOSTIC_RULES["ALEMBIC_MULTIPLE_HEADS"]

    if "can't locate revision" in err_str or "revision not found" in err_str:
        return DIAGNOSTIC_RULES["ALEMBIC_REVISION_NOT_FOUND"]

    if "diverged" in err_str or "history divergence" in err_str:
        return DIAGNOSTIC_RULES["ALEMBIC_HISTORY_DIVERGED"]

    # Generic fallback rule
    return DiagnosticRule(
        code="GENERIC_DATABASE_ERROR",
        title="Unclassified Database Error",
        what_happened=f"Database operation failed with error: {str(exc)}",
        why_it_happened="The database driver returned an error condition.",
        risk="MEDIUM: Operation failed.",
        what_not_to_do="Do NOT execute unverified SQL queries in production.",
        recommended_fix="Review the error message, inspect active migrations, and check connection settings.",
        safe_command="dbx doctor",
        severity="MEDIUM",
    )
