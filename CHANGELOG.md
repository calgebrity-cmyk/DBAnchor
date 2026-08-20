# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-08-20

### Added
- Core `Database` / `DBAnchor` middleware with sync and async SQLAlchemy engine and session management.
- Comprehensive `DATABASE_URL` parser, driver normalizer, and password encoding diagnostic.
- Deterministic diagnostic engine with rule catalog for PostgreSQL and Alembic error states.
- Provider detection for Supabase, Neon, Railway, AWS RDS, GCP Cloud SQL, Azure, and Local Docker.
- Environment detector for `development`, `test`, `staging`, and `production`.
- Project and framework detector (FastAPI, Django, Flask, SQLAlchemy, Alembic, Docker).
- Health check runner with DNS, TCP, handshake, SSL, authentication, permissions, and schema checks.
- Schema reflection, snapshotting, and drift detection between application metadata and live PostgreSQL.
- Safe migration engine with destructive DDL detection (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`), risk scoring, dry-run planning, and production safety guards.
- Project adoption engine (`dbx adopt`) for unmanaged legacy databases.
- Local Docker PostgreSQL lifecycle management (`dbx local start|stop|reset|status`).
- Dual CLI commands: `dbanchor` and `dbx` with interactive rich formatting and machine-readable `--json` output.
