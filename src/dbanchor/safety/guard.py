"""Production safety guards enforcing safe migration workflows."""

from __future__ import annotations

from dbanchor.environments.detector import EnvironmentTier
from dbanchor.safety.models import RiskLevel, SafetyAssessment


class SafetyGuardError(Exception):
    """Raised when an operation is blocked by safety guardrails."""
    def __init__(self, assessment: SafetyAssessment, message: str) -> None:
        super().__init__(message)
        self.assessment = assessment


class SafetyGuard:
    """Evaluates safety policies and blocks dangerous executions in production."""

    @staticmethod
    def enforce(
        assessment: SafetyAssessment,
        environment: EnvironmentTier,
        force_destructive: bool = False,
    ) -> None:
        """Enforce safety rules based on environment tier and destructive risk."""
        if not assessment.is_destructive:
            return

        if force_destructive:
            return

        # In production/staging, block destructive operations automatically
        if environment.is_production_like:
            ops_summary = "\n".join(
                f"  - [{op.risk_level.value}] {op.operation_type.value}: {op.target_object} ({op.reason})"
                for op in assessment.operations
            )
            msg = (
                f"Execution BLOCKED: Destructive database operations detected in {environment.value.upper()} environment.\n"
                f"Risk Level: {assessment.overall_risk.value}\n\n"
                f"Flagged operations:\n{ops_summary}\n\n"
                f"To execute with explicit confirmation, review 'dbx migration plan' then pass '--force-destructive'."
            )
            raise SafetyGuardError(assessment, msg)
