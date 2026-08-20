"""Integration tests for connection engine and TCP check."""

from dbanchor.config.models import ConnectionConfig
from dbanchor.connection.connector import DatabaseConnector, test_tcp_connectivity as check_tcp_socket
from dbanchor.connection.url import parse_connection_url


def test_tcp_connectivity_unreachable():
    # Test invalid host
    ok, latency, err = check_tcp_socket("non-existent-domain-xyz-12345.local", 5432, timeout=0.5)
    assert ok is False
    assert err is not None


def test_connector_initialization():
    url = "postgresql://testuser:testpass@localhost:5432/mydb"
    info = parse_connection_url(url)
    config = ConnectionConfig(url=url)
    connector = DatabaseConnector(config, info)

    assert connector.connection_info.port == 5432
    assert connector.config.pool_size == 5
