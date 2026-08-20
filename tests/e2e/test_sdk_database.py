"""E2E tests for the Database / DBAnchor SDK class."""

from dbanchor.core.database import Database, DBAnchor
from dbanchor.providers.models import ProviderType


def test_database_sdk_instantiation_and_properties(sample_supabase_url: str):
    db = Database(url=sample_supabase_url)
    assert db.safe_url is not None
    assert "mypassword" not in db.safe_url
    assert "********" in db.safe_url

    provider = db.get_provider()
    assert provider.provider_type == ProviderType.SUPABASE

    diag = db.diagnose("password authentication failed for user 'postgres'")
    assert diag.code == "AUTH_FAILED"
    assert "28P01" in diag.title or "Authentication" in diag.title


def test_dbanchor_alias():
    assert DBAnchor is Database
    db = DBAnchor(url="postgresql://user:pass@localhost:5432/mydb")
    assert db.conn_info.database == "mydb"
