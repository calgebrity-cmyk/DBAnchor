"""Deterministic diagnostic rule catalog for PostgreSQL and Alembic error conditions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DiagnosticRule:
    """Standardized deterministic diagnostic explanation rule."""
    code: str
    title: str
    what_happened: str
    why_it_happened: str
    risk: str
    what_not_to_do: str
    recommended_fix: str
    safe_command: Optional[str] = None
    severity: str = "HIGH"


DIAGNOSTIC_RULES: dict[str, DiagnosticRule] = {
    "AUTH_FAILED": DiagnosticRule(
        code="AUTH_FAILED",
        title="PostgreSQL Authentication Failed (SQLSTATE 28P01 / 28000)",
        what_happened="The PostgreSQL server is reachable on the specified port, but rejected the credentials provided in DATABASE_URL.",
        why_it_happened=(
            "1. Incorrect username or password.\n"
            "2. The password contains special characters (like '@', ':', '#', '%', '?') that were not URL-encoded.\n"
            "3. Database user credentials were rotated or changed on the host/provider.\n"
            "4. The user exists but does not have login permissions for this database."
        ),
        risk="LOW: No database changes were made. Access is currently blocked.",
        what_not_to_do="Do NOT change pg_hba.conf to 'trust' in production or commit plain-text credentials to version control.",
        recommended_fix=(
            "1. Double-check your password in .env.\n"
            "2. If your password contains special characters, URL-encode them (e.g. 'p@ss' -> 'p%40ss').\n"
            "3. Verify login directly via psql: psql -U <user> -h <host> -d <db>"
        ),
        safe_command="dbx connect",
        severity="HIGH",
    ),
    "CONNECTION_REFUSED": DiagnosticRule(
        code="CONNECTION_REFUSED",
        title="Connection Refused (Port Unreachable)",
        what_happened="The client attempted to open a TCP connection to the host/port, but no service is listening on that port or a firewall blocked the connection.",
        why_it_happened=(
            "1. The local PostgreSQL service or Docker container is not running.\n"
            "2. The port number in DATABASE_URL is wrong (default is 5432).\n"
            "3. PostgreSQL is bound to localhost (127.0.0.1) and you are attempting to connect from a container or remote host.\n"
            "4. A firewall / AWS Security Group is blocking inbound traffic on the port."
        ),
        risk="LOW: No connection made. Zero impact on data.",
        what_not_to_do="Do NOT modify firewall rules to allow all traffic (0.0.0.0/0) without proper network access controls.",
        recommended_fix=(
            "1. For local development, start PostgreSQL container: dbx local start\n"
            "2. If using Docker, check container status: docker ps\n"
            "3. Verify PostgreSQL is listening: pg_isready -h <host> -p <port>"
        ),
        safe_command="dbx local start",
        severity="HIGH",
    ),
    "HOST_UNREACHABLE": DiagnosticRule(
        code="HOST_UNREACHABLE",
        title="Host Unreachable or DNS Resolution Failed",
        what_happened="The database hostname could not be resolved by DNS or the network route timed out.",
        why_it_happened=(
            "1. Typo in hostname (e.g. 'db.xyzz.supabase.co').\n"
            "2. No active internet connection or DNS resolver issue.\n"
            "3. Cloud database instance was deleted, paused, or suspended.\n"
            "4. Connecting across private networks (VPC) without VPN or peering."
        ),
        risk="LOW: Application cannot reach the server. No data corrupted.",
        what_not_to_do="Do NOT hardcode temporary IP addresses in production config.",
        recommended_fix=(
            "1. Verify internet connectivity and DNS lookup: nslookup <hostname>\n"
            "2. Check cloud provider dashboard (Supabase / Neon / Railway / AWS) to ensure instance is ACTIVE."
        ),
        safe_command="dbx doctor",
        severity="HIGH",
    ),
    "DATABASE_NOT_FOUND": DiagnosticRule(
        code="DATABASE_NOT_FOUND",
        title="Database Does Not Exist (SQLSTATE 3D000)",
        what_happened="The PostgreSQL server is online and credentials are valid, but the target database specified in the URL path does not exist on the server.",
        why_it_happened=(
            "1. Typo in the database name in DATABASE_URL (e.g. '/mydb_dev' vs '/mydb').\n"
            "2. The database has not been created yet on a fresh server or container.\n"
            "3. Default database 'postgres' was expected."
        ),
        risk="LOW: Zero data loss. Just need to create the database.",
        what_not_to_do="Do NOT drop and recreate existing databases.",
        recommended_fix=(
            "1. Connect to default 'postgres' database and create target database:\n"
            "   CREATE DATABASE <dbname>;"
        ),
        safe_command="dbx doctor",
        severity="MEDIUM",
    ),
    "SSL_REQUIRED_OR_FAILED": DiagnosticRule(
        code="SSL_REQUIRED_OR_FAILED",
        title="SSL / TLS Connection Negotiation Failed",
        what_happened="The database server requires an encrypted SSL connection, or the client rejected the server's certificate.",
        why_it_happened=(
            "1. Managed cloud databases (Supabase, Neon, Railway, RDS) strictly enforce SSL/TLS encryption.\n"
            "2. DATABASE_URL is missing '?sslmode=require' query parameter.\n"
            "3. Self-signed certificate cannot be verified without CA certificate."
        ),
        risk="LOW: Connection rejected before any queries were executed.",
        what_not_to_do="Do NOT disable SSL verification in production environments.",
        recommended_fix=(
            "Append '?sslmode=require' to your DATABASE_URL in .env."
        ),
        safe_command="dbx doctor",
        severity="HIGH",
    ),
    "PERMISSION_DENIED": DiagnosticRule(
        code="PERMISSION_DENIED",
        title="Permission Denied (SQLSTATE 42501)",
        what_happened="The authenticated database user does not have sufficient privileges to perform the requested operation on the target schema or table.",
        why_it_happened=(
            "1. User is missing CREATE, USAGE, or DDL privileges on schema 'public'.\n"
            "2. Database ownership was assigned to a different role/user.\n"
            "3. Read-only user account is being used to run migrations."
        ),
        risk="MEDIUM: Migration or write operations will fail.",
        what_not_to_do="Do NOT grant superuser privileges indiscriminately to application roles.",
        recommended_fix=(
            "Grant necessary permissions to the application user:\n"
            "GRANT ALL PRIVILEGES ON SCHEMA public TO <user>;\n"
            "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO <user>;"
        ),
        safe_command="dbx doctor",
        severity="HIGH",
    ),
    "TABLE_NOT_FOUND": DiagnosticRule(
        code="TABLE_NOT_FOUND",
        title="Relation / Table Does Not Exist (SQLSTATE 42P01)",
        what_happened="The query or migration references a table that does not exist in the active schema.",
        why_it_happened=(
            "1. Pending migrations have not yet been applied to the database.\n"
            "2. Migration execution order is incorrect (a table is referenced before its CREATE TABLE migration ran).\n"
            "3. Query is targeting the wrong PostgreSQL search_path / schema."
        ),
        risk="MEDIUM: Queries referencing this table will fail with 500 errors.",
        what_not_to_do="Do NOT manually create ad-hoc tables in production without an Alembic migration script.",
        recommended_fix=(
            "1. Check pending migrations: dbx migration status\n"
            "2. Safely apply pending migrations: dbx migrate"
        ),
        safe_command="dbx migrate",
        severity="HIGH",
    ),
    "COLUMN_NOT_FOUND": DiagnosticRule(
        code="COLUMN_NOT_FOUND",
        title="Column Does Not Exist (SQLSTATE 42703)",
        what_happened="An SQL query or migration attempted to access or modify a column that is not present on the table.",
        why_it_happened=(
            "1. Schema drift between application models and live PostgreSQL schema.\n"
            "2. Migration adding this column has not been executed on this database.\n"
            "3. The column was renamed in Python models without generating an Alembic migration."
        ),
        risk="MEDIUM: Application queries will fail at runtime.",
        what_not_to_do="Do NOT manually alter production tables without tracking changes in version control.",
        recommended_fix=(
            "1. Compare schema differences: dbx schema diff\n"
            "2. Run pending migrations: dbx migrate"
        ),
        safe_command="dbx schema diff",
        severity="HIGH",
    ),
    "DUPLICATE_OBJECT": DiagnosticRule(
        code="DUPLICATE_OBJECT",
        title="Object Already Exists (SQLSTATE 42P07 / 42701 / 42710)",
        what_happened="A migration attempted to create a table, column, index, or constraint that already exists in the database.",
        why_it_happened=(
            "1. The database was partially migrated or restored from a backup out-of-sync with alembic_version.\n"
            "2. Manual schema modifications were made outside of Alembic.\n"
            "3. Alembic migration history was stamped incorrectly."
        ),
        risk="HIGH: Migration aborted midway. Potential for partial migration state.",
        what_not_to_do="Do NOT run 'alembic stamp head' blindly without inspecting what differences exist.",
        recommended_fix=(
            "1. Inspect schema vs model drift: dbx schema diff\n"
            "2. Check migration status: dbx migration status\n"
            "3. For existing databases, consider adopting cleanly: dbx adopt"
        ),
        safe_command="dbx schema diff",
        severity="HIGH",
    ),
    "ALEMBIC_MULTIPLE_HEADS": DiagnosticRule(
        code="ALEMBIC_MULTIPLE_HEADS",
        title="Alembic Multiple Migration Heads Detected",
        what_happened="Alembic detected multiple branches / leaves in the migration revision graph. Two developers created migrations from the same parent revision.",
        why_it_happened=(
            "Two git branches were merged, each containing a new migration script descending from the same base revision, creating a fork."
        ),
        risk="HIGH: Database cannot determine which migration path to execute automatically.",
        what_not_to_do="Do NOT delete migration files or force stamp without merging heads.",
        recommended_fix=(
            "Create an Alembic merge revision to unify the branches:\n"
            "alembic merge heads -m 'merge conflicting heads'"
        ),
        safe_command="dbx migration explain",
        severity="CRITICAL",
    ),
    "ALEMBIC_REVISION_NOT_FOUND": DiagnosticRule(
        code="ALEMBIC_REVISION_NOT_FOUND",
        title="Missing Migration Revision File",
        what_happened="The database's alembic_version table contains a revision ID that does not exist in the local migrations/versions directory.",
        why_it_happened=(
            "1. A migration file was deleted or renamed in git.\n"
            "2. Connecting to a database that was migrated on a different git branch.\n"
            "3. Uncommitted migration on another machine was applied to this shared database."
        ),
        risk="CRITICAL: Alembic cannot calculate the upgrade/downgrade path.",
        what_not_to_do="Do NOT delete the alembic_version table.",
        recommended_fix=(
            "1. Check git branch or recover the missing migration file.\n"
            "2. Run 'dbx migration status' to see current database revision."
        ),
        safe_command="dbx migration status",
        severity="CRITICAL",
    ),
    "ALEMBIC_HISTORY_DIVERGED": DiagnosticRule(
        code="ALEMBIC_HISTORY_DIVERGED",
        title="Migration History Diverged",
        what_happened="The migration revision recorded in the live database is neither an ancestor nor a descendant of the current local codebase heads.",
        why_it_happened=(
            "1. Database was migrated from a separate feature branch.\n"
            "2. Migration files were rewritten or squashed after being applied to the live database."
        ),
        risk="HIGH: Standard 'alembic upgrade head' will fail or behave unpredictably.",
        what_not_to_do="Do NOT run 'alembic stamp head' without running 'dbx schema diff' first.",
        recommended_fix=(
            "1. Inspect differences: dbx schema diff\n"
            "2. Run adoption workflow: dbx adopt"
        ),
        safe_command="dbx adopt",
        severity="HIGH",
    ),
    "UNENCODED_PASSWORD_SPECIAL_CHARS": DiagnosticRule(
        code="UNENCODED_PASSWORD_SPECIAL_CHARS",
        title="URL Password Contains Unencoded Special Characters",
        what_happened="The DATABASE_URL contains reserved URI characters in the password (such as '@', ':', '#', '%', '?').",
        why_it_happened=(
            "Standard URI parsing treats '@' as the delimiter between user:pass and host:port. If the password has '@', the parser misinterprets the host."
        ),
        risk="LOW: Simple formatting error in .env. No data corrupted.",
        what_not_to_do="Do NOT share unencoded credentials in chat logs or issues.",
        recommended_fix=(
            "Use urllib.parse.quote_plus to encode your password:\n"
            "python -c \"import urllib.parse; print(urllib.parse.quote_plus('your_password'))\"\n"
            "Then update DATABASE_URL with the encoded password."
        ),
        safe_command="dbx config check",
        severity="HIGH",
    ),
}
