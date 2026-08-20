"""DDL and SQL safety analyzer for detecting destructive database changes."""

from __future__ import annotations

import re
from dbanchor.safety.models import (
    DestructiveOperation,
    OperationType,
    RiskLevel,
    SafetyAssessment,
)

# Regex patterns for destructive DDL
DROP_TABLE_PATTERN = re.compile(r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([^\s;,\(]+)", re.IGNORECASE)
DROP_COLUMN_PATTERN = re.compile(
    r"\bALTER\s+TABLE\s+([^\s;,\(]+)\s+DROP\s+(?:COLUMN\s+)?([^\s;,\(]+)",
    re.IGNORECASE,
)
TRUNCATE_PATTERN = re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?([^\s;,\(]+)", re.IGNORECASE)
ALTER_TYPE_PATTERN = re.compile(
    r"\bALTER\s+TABLE\s+([^\s;,\(]+)\s+ALTER\s+(?:COLUMN\s+)?([^\s;,\(]+)\s+TYPE\s+([^\s;,\(]+)",
    re.IGNORECASE,
)
DROP_DATABASE_PATTERN = re.compile(r"\bDROP\s+DATABASE\s+([^\s;,\(]+)", re.IGNORECASE)
DROP_SCHEMA_PATTERN = re.compile(r"\bDROP\s+SCHEMA\s+([^\s;,\(]+)", re.IGNORECASE)
CREATE_INDEX_PATTERN = re.compile(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?([^\s;,\(]+)\s+ON\s+([^\s;,\(]+)", re.IGNORECASE)


def analyze_sql_safety(sql_text: str) -> SafetyAssessment:
    """Analyze raw SQL statements for destructive DDL operations and return SafetyAssessment."""
    if not sql_text or not sql_text.strip():
        return SafetyAssessment(overall_risk=RiskLevel.LOW, is_destructive=False)

    flagged_ops: list[DestructiveOperation] = []
    warnings: list[str] = []

    # 1. DROP DATABASE
    for match in DROP_DATABASE_PATTERN.finditer(sql_text):
        target = match.group(1)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.DROP_TABLE,
                target_object=target,
                sql_snippet=match.group(0),
                risk_level=RiskLevel.CRITICAL,
                reason=f"Drops entire database '{target}'. Permanent irreversible data loss.",
            )
        )

    # 2. DROP SCHEMA
    for match in DROP_SCHEMA_PATTERN.finditer(sql_text):
        target = match.group(1)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.DROP_TABLE,
                target_object=target,
                sql_snippet=match.group(0),
                risk_level=RiskLevel.CRITICAL,
                reason=f"Drops schema '{target}' and all contained tables and data.",
            )
        )

    # 3. DROP TABLE
    for match in DROP_TABLE_PATTERN.finditer(sql_text):
        table_name = match.group(1)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.DROP_TABLE,
                target_object=table_name,
                sql_snippet=match.group(0),
                risk_level=RiskLevel.CRITICAL,
                reason=f"Permanently drops table '{table_name}' and all its rows.",
            )
        )

    # 4. DROP COLUMN
    for match in DROP_COLUMN_PATTERN.finditer(sql_text):
        table_name = match.group(1)
        col_name = match.group(2)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.DROP_COLUMN,
                target_object=f"{table_name}.{col_name}",
                sql_snippet=match.group(0),
                risk_level=RiskLevel.HIGH,
                reason=f"Permanently deletes column '{col_name}' from '{table_name}'. Data cannot be recovered.",
            )
        )

    # 5. TRUNCATE
    for match in TRUNCATE_PATTERN.finditer(sql_text):
        table_name = match.group(1)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.TRUNCATE,
                target_object=table_name,
                sql_snippet=match.group(0),
                risk_level=RiskLevel.CRITICAL,
                reason=f"Empties table '{table_name}'. All data deleted.",
            )
        )

    # 6. ALTER COLUMN TYPE
    for match in ALTER_TYPE_PATTERN.finditer(sql_text):
        table_name = match.group(1)
        col_name = match.group(2)
        new_type = match.group(3)
        flagged_ops.append(
            DestructiveOperation(
                operation_type=OperationType.ALTER_TYPE,
                target_object=f"{table_name}.{col_name}",
                sql_snippet=match.group(0),
                risk_level=RiskLevel.MEDIUM,
                reason=f"Changes datatype of '{table_name}.{col_name}' to '{new_type}'. May require table rewrite and lock.",
            )
        )

    # 7. Non-concurrent index creation on large tables
    for match in CREATE_INDEX_PATTERN.finditer(sql_text):
        snippet = match.group(0)
        table_name = match.group(2)
        if "CONCURRENTLY" not in snippet.upper():
            warnings.append(
                f"Index created non-concurrently on '{table_name}'. In production with active traffic, consider CREATE INDEX CONCURRENTLY."
            )

    # Determine overall risk
    if any(op.risk_level == RiskLevel.CRITICAL for op in flagged_ops):
        overall = RiskLevel.CRITICAL
    elif any(op.risk_level == RiskLevel.HIGH for op in flagged_ops):
        overall = RiskLevel.HIGH
    elif any(op.risk_level == RiskLevel.MEDIUM for op in flagged_ops):
        overall = RiskLevel.MEDIUM
    else:
        overall = RiskLevel.LOW

    is_destructive = len(flagged_ops) > 0

    return SafetyAssessment(
        overall_risk=overall,
        is_destructive=is_destructive,
        operations=flagged_ops,
        can_auto_execute=not is_destructive,
        warnings=warnings,
    )
