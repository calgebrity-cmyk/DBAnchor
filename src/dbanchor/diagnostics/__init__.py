"""Deterministic diagnostics and error remediation for DBAnchor."""

from dbanchor.diagnostics.classifier import classify_exception
from dbanchor.diagnostics.engine import DiagnosticEngine, DiagnosticExplanation
from dbanchor.diagnostics.rules import DIAGNOSTIC_RULES, DiagnosticRule

__all__ = [
    "DiagnosticRule",
    "DIAGNOSTIC_RULES",
    "DiagnosticExplanation",
    "DiagnosticEngine",
    "classify_exception",
]
