"""Unit tests for DDL safety analyzer."""

from dbanchor.safety.analyzer import analyze_sql_safety
from dbanchor.safety.models import OperationType, RiskLevel


def test_safe_table_creation():
    sql = """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    """
    assessment = analyze_sql_safety(sql)
    assert assessment.overall_risk == RiskLevel.LOW
    assert assessment.is_destructive is False
    assert len(assessment.operations) == 0


def test_destructive_drop_table():
    sql = "DROP TABLE users CASCADE;"
    assessment = analyze_sql_safety(sql)
    assert assessment.overall_risk == RiskLevel.CRITICAL
    assert assessment.is_destructive is True
    assert any(op.operation_type == OperationType.DROP_TABLE for op in assessment.operations)


def test_destructive_drop_column():
    sql = "ALTER TABLE users DROP COLUMN phone;"
    assessment = analyze_sql_safety(sql)
    assert assessment.overall_risk == RiskLevel.HIGH
    assert assessment.is_destructive is True
    assert any(op.operation_type == OperationType.DROP_COLUMN for op in assessment.operations)


def test_destructive_truncate():
    sql = "TRUNCATE TABLE logs;"
    assessment = analyze_sql_safety(sql)
    assert assessment.overall_risk == RiskLevel.CRITICAL
    assert assessment.is_destructive is True


def test_medium_risk_alter_column_type():
    sql = "ALTER TABLE users ALTER COLUMN email TYPE TEXT;"
    assessment = analyze_sql_safety(sql)
    assert assessment.overall_risk == RiskLevel.MEDIUM
    assert assessment.is_destructive is True
