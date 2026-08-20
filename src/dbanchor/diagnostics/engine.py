"""Diagnostic engine orchestrating diagnostic analysis and remediation output."""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field
from dbanchor.diagnostics.classifier import classify_exception
from dbanchor.diagnostics.rules import DiagnosticRule


class DiagnosticExplanation(BaseModel):
    """Structured diagnostic result for developers and machine-readable output."""
    code: str
    title: str
    what_happened: str
    why_it_happened: str
    risk: str
    what_not_to_do: str
    recommended_fix: str
    safe_command: Optional[str] = None
    severity: str = "HIGH"


class DiagnosticEngine:
    """Explains database and migration errors deterministically."""

    @staticmethod
    def diagnose_error(
        exc: Exception | str,
        context: Optional[dict[str, Any]] = None,
    ) -> DiagnosticExplanation:
        """Produce a structured, actionable diagnosis for an exception."""
        rule: DiagnosticRule = classify_exception(exc, context)
        return DiagnosticExplanation(
            code=rule.code,
            title=rule.title,
            what_happened=rule.what_happened,
            why_it_happened=rule.why_it_happened,
            risk=rule.risk,
            what_not_to_do=rule.what_not_to_do,
            recommended_fix=rule.recommended_fix,
            safe_command=rule.safe_command,
            severity=rule.severity,
        )
