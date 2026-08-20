"""Unit tests for database provider detection."""

from dbanchor.connection.url import parse_connection_url
from dbanchor.providers.detector import detect_provider
from dbanchor.providers.models import ProviderType


def test_detect_supabase():
    url = "postgresql://postgres:pass@db.xyz.supabase.co:5432/postgres"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.name == "Supabase"
    assert provider.provider_type == ProviderType.SUPABASE
    assert provider.requires_ssl is True
    assert provider.is_connection_pooled is False


def test_detect_supabase_pooler():
    url = "postgresql://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.SUPABASE
    assert provider.is_connection_pooled is True


def test_detect_neon():
    url = "postgresql://user:pass@ep-cool-fog-123.us-east-2.aws.neon.tech/neondb"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.name == "Neon"
    assert provider.provider_type == ProviderType.NEON
    assert provider.is_serverless is True
    assert provider.requires_ssl is True


def test_detect_railway():
    url = "postgresql://postgres:pass@roundhouse.proxy.rlwy.net:12345/railway"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.RAILWAY


def test_detect_aws_rds():
    url = "postgresql://master:pass@my-db.c9ak4b1.us-west-2.rds.amazonaws.com:5432/mydb"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.AWS_RDS
    assert "AWS" in provider.name


def test_detect_gcp_cloudsql():
    url = "postgresql://user:pass@my-instance.cloudsql.goog:5432/mydb"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.GCP_CLOUDSQL


def test_detect_localhost():
    url = "postgresql://user:pass@127.0.0.1:5432/test"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.LOCALHOST


def test_detect_generic_fallback():
    url = "postgresql://user:pass@my-custom-server.internal:5432/db"
    info = parse_connection_url(url)
    provider = detect_provider(info)
    assert provider.provider_type == ProviderType.GENERIC
    assert provider.name == "Generic PostgreSQL"
