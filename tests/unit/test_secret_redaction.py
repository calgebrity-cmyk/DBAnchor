"""Unit tests for secret and password redaction."""

from dbanchor.output.redaction import redact_secrets, redact_url, sanitize_data_dict


def test_redact_url():
    url = "postgresql://myuser:super_secret_pw123@db.supabase.co:5432/postgres"
    redacted = redact_url(url)
    assert "super_secret_pw123" not in redacted
    assert "********" in redacted
    assert "myuser" in redacted
    assert "db.supabase.co" in redacted


def test_redact_secrets_in_error_strings():
    err_msg = "Failed connecting to postgresql://admin:p@ssw0rd!@10.0.0.1:5432/app with password='my_api_key_123'"
    redacted = redact_secrets(err_msg)
    assert "p@ssw0rd!" not in redacted
    assert "my_api_key_123" not in redacted
    assert "********" in redacted


def test_sanitize_data_dict_recursive():
    payload = {
        "status": "ok",
        "database_url": "postgresql://user:secret123@localhost:5432/db",
        "config": {
            "password": "plain_text_password",
            "token": "bearer_abc_123",
            "host": "localhost",
        },
        "items": [
            {"password": "nested_secret", "name": "item1"},
        ],
    }

    sanitized = sanitize_data_dict(payload)
    assert "secret123" not in str(sanitized)
    assert "plain_text_password" not in str(sanitized)
    assert "bearer_abc_123" not in str(sanitized)
    assert "nested_secret" not in str(sanitized)
    assert sanitized["config"]["password"] == "********"
    assert sanitized["items"][0]["password"] == "********"
