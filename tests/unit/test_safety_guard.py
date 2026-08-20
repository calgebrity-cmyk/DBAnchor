"""Unit tests for SafetyGuard production blocking and enforcement."""

import pytest
from dbanchor.environments.detector import EnvironmentTier
from dbanchor.safety.analyzer import analyze_sql_safety
from dbanchor.safety.guard import SafetyGuard, SafetyGuardError


def test_guard_allows_safe_operations_in_production():
    sql = "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT);"
    assessment = analyze_sql_safety(sql)
    # Should not raise
    SafetyGuard.enforce(assessment, EnvironmentTier.PRODUCTION, force_destructive=False)


def test_guard_blocks_destructive_in_production():
    sql = "DROP TABLE users;"
    assessment = analyze_sql_safety(sql)
    with pytest.raises(SafetyGuardError, match="Execution BLOCKED"):
        SafetyGuard.enforce(assessment, EnvironmentTier.PRODUCTION, force_destructive=False)


def test_guard_allows_destructive_with_force_flag():
    sql = "DROP TABLE users;"
    assessment = analyze_sql_safety(sql)
    # With force_destructive=True, should not raise
    SafetyGuard.enforce(assessment, EnvironmentTier.PRODUCTION, force_destructive=True)


def test_guard_allows_destructive_in_development():
    sql = "DROP TABLE users;"
    assessment = analyze_sql_safety(sql)
    # In development, it warns but does not raise
    SafetyGuard.enforce(assessment, EnvironmentTier.DEVELOPMENT, force_destructive=False)
