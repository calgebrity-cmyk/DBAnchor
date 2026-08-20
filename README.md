<p align="center">
  <img src="assets/logos/dbanchor-logo.png" alt="DBAnchor Logo" width="320" />
</p>

# DBAnchor

**Safe Universal Database Developer-Experience Middleware & Diagnostics for PostgreSQL.**

<p align="center">
  <a href="https://dbanchor.calgebrity.com/"><strong>dbanchor.calgebrity.com</strong></a>
</p>

[![CI](https://github.com/calgebrity-cmyk/DBAnchor/actions/workflows/ci.yml/badge.svg)](https://github.com/calgebrity-cmyk/DBAnchor/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/badge/pypi-0.1.0-blue.svg)](https://pypi.org/project/dbanchor/)
[![Python versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://pypi.org/project/dbanchor/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-dbanchor.calgebrity.com-blue.svg)](https://dbanchor.calgebrity.com/)

---


## 🎯 The Problem

Connecting Python applications to PostgreSQL, diagnosing credential or SSL errors, synchronizing Alembic migrations, and preventing accidental schema drift across local, staging, and cloud providers (Supabase, Neon, Railway, AWS RDS) is notoriously repetitive and error-prone:

- ❌ Unencoded special characters in passwords (e.g. `@`, `#`, `%`, `?`) break URL parsers silently.
- ❌ Cloud providers enforce SSL requirements that throw cryptic handshake errors.
- ❌ Alembic migrations diverged or multiple heads block deployments.
- ❌ Accidental destructive DDL (`DROP COLUMN`, `DROP TABLE`) executed in production destroys data.
- ❌ Cryptic error codes (`SQLSTATE 28P01`, `42P01`, `08006`) waste hours of developer debugging time.

---

## 💡 The Solution

**DBAnchor** is a lightweight, zero-boilerplate developer-experience middleware and control layer between your application and PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
```

```python
from dbanchor import Database

db = Database()
```

DBAnchor automatically:
1. **Reads and normalizes `DATABASE_URL`** with automatic special-character password encoding diagnostics.
2. **Detects hosting providers** (Supabase, Neon, Railway, AWS RDS, GCP Cloud SQL, Docker).
3. **Conducts non-destructive health checks** (DNS, TCP, SSL, Handshake, Auth, Permissions, Schema).
4. **Inspects Alembic migration states** (head revisions, pending steps, multi-head conflicts, divergence).
5. **Detects schema drift** between application SQLAlchemy models and live PostgreSQL tables.
6. **Enforces production safety gates** (blocks destructive operations without explicit confirmation).
7. **Explains errors deterministically** with senior-engineer root-cause analysis and safe fixes.

---

## 🛡️ Product Philosophy

> **DBAnchor does NOT replace PostgreSQL, SQLAlchemy, Alembic, or Cloud Providers.**
> It is **NOT** an invasive controller. It is a **safe developer companion** that understands your database problems, explains why issues occur, guides safe remediation, and protects your data against accidental loss.

- **Zero Data Loss First**: Destructive changes (`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`) are strictly blocked in production without explicit confirmation.
- **100% Deterministic & Offline**: No external AI/LLM API calls. Diagnostics rely on comprehensive AST/SQL analysis and a deterministic knowledge base.
- **Zero Credential Leaks**: Database passwords and secrets are redacted across all logs, tables, JSON exports, and tracebacks.

---

## 🚀 5-Minute Quickstart

### 1. Installation

```bash
pip install dbanchor
```

*(Optional PostgreSQL driver bundles)*:
```bash
pip install "dbanchor[psycopg]"   # Psycopg 3
pip install "dbanchor[asyncpg]"   # Asyncpg for async engines
```

### 2. Configure Environment (`.env`)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app_db
APP_ENV=development
```

### 3. Run Doctor Diagnostics

```bash
dbx doctor
# or
dbanchor doctor
```

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
             DBAnchor Database Doctor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Provider       : Supabase
 Environment    : DEVELOPMENT
 Database Engine: PostgreSQL 17.0
 Host           : db.xyz.supabase.co
 Target DB      : postgres
 Active User    : postgres
 Health Status  : READY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ✓ PASS  DNS Resolution               (2.4 ms)
 ✓ PASS  TCP Reachability             (14.1 ms)
 ✓ PASS  Authentication & Handshake   (32.8 ms)
 ✓ PASS  Schema Permissions           (5.1 ms)
 ✓ PASS  Migration System             (1.2 ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: READY
```

---

## 💻 Python SDK

### Sync Usage (SQLAlchemy ORM)

```python
from dbanchor import Database
from sqlalchemy import select
from myapp.models import User

# Automatically loads .env and initializes engine & connection pool
db = Database()

# Context-managed session (auto-commits on success, rolls back on error)
with db.session() as session:
    users = session.scalars(select(User)).all()
```

### Async Usage (FastAPI / AsyncIO)

```python
from dbanchor import Database
from sqlalchemy import select
from myapp.models import User

db = Database()

async def get_users():
    async with db.async_session() as session:
        result = await session.scalars(select(User))
        return result.all()
```

### Programmatic Health Checks & Diagnostics

```python
# Check health
report = db.check_health()
if not report.is_healthy:
    print(f"Database degraded: {report.summary}")

# Detect provider
provider = db.get_provider()
print(f"Running on {provider.name} (Serverless: {provider.is_serverless})")

# Deterministic error explanation
try:
    with db.session() as session:
        ...
except Exception as e:
    explanation = db.diagnose(e)
    print(explanation.what_happened)
    print(explanation.recommended_fix)
```

---

## 🛠️ CLI Reference (`dbx` / `dbanchor`)

| Command | Description |
| ------- | ----------- |
| `dbx doctor` | Comprehensive health check (DNS, TCP, Auth, SSL, Permissions, Migrations) |
| `dbx doctor --json` | Machine-readable health status and metrics for CI/CD |
| `dbx connect` | Instant connection verification and ping latency |
| `dbx status` | Unified status card of provider, connection, and migration heads |
| `dbx init` | Inspects project framework (FastAPI, Django, SQLAlchemy) and generates `.env` |
| `dbx migrate` | Safely applies pending migrations (dry-run plan + safety gates) |
| `dbx migrate --dry-run` | Previews pending migration operations and evaluates risk |
| `dbx migration status` | Shows current database revision vs codebase heads |
| `dbx migration plan` | Detailed dry-run plan identifying destructive DDL |
| `dbx migration explain <err>` | Explains migration conflicts, divergence, or multiple heads |
| `dbx schema inspect` | Reflects live database tables, columns, indexes, and constraints |
| `dbx schema diff` | Compares live database schema against application SQLAlchemy models |
| `dbx config check` | Validates configuration and checks for unencoded password special characters |
| `dbx provider detect` | Detects hosting platform (Supabase, Neon, Railway, AWS RDS, Cloud SQL) |
| `dbx adopt` | Adopts existing databases into Alembic without deleting or altering data |
| `dbx local start` | Starts local PostgreSQL container in Docker |
| `dbx local stop` | Stops local PostgreSQL container |
| `dbx local reset` | Safely resets local Docker container with confirmation |
| `dbx version` | Displays version and installed ecosystem drivers |

---

## 🔒 Safety Guardrails & Destructive DDL Protection

Before running migrations, DBAnchor parses and analyzes proposed DDL statements:

| Operation | Risk Level | Production Execution Policy |
| --------- | ---------- | --------------------------- |
| `CREATE TABLE` / `ADD COLUMN (nullable)` | **LOW** | Auto-allowed |
| `CREATE INDEX (non-concurrent)` | **MEDIUM** | Warns on potential table lock |
| `ALTER TABLE ... DROP COLUMN` | **HIGH** | **BLOCKED** without `--force-destructive` |
| `DROP TABLE` / `TRUNCATE` / `DROP SCHEMA` | **CRITICAL** | **BLOCKED** without `--force-destructive` |

Example Diagnostic on Destructive Migration:

```text
Execution BLOCKED: Destructive database operations detected in PRODUCTION environment.
Risk Level: HIGH

Flagged operations:
  - [HIGH] DROP_COLUMN: users.phone (Permanently deletes column 'phone' from 'users')

To execute with explicit confirmation, review 'dbx migration plan' then pass '--force-destructive'.
```

---

## 🧠 Deterministic Error Intelligence

DBAnchor translates cryptic PostgreSQL SQLSTATE codes and Alembic exceptions into actionable senior-engineer advice:

- **SQLSTATE `28P01` / `28000` (Auth Failed)**: Detects incorrect credentials, rotated provider tokens, or unencoded `@` / `#` characters.
- **SQLSTATE `3D000` (Database Missing)**: Identifies missing target database on server.
- **SQLSTATE `42P01` (Relation Missing)**: Pinpoints out-of-order migrations or missing tables.
- **SQLSTATE `42703` (Column Missing)**: Flags schema drift between Python models and live DB.
- **Alembic Multiple Heads**: Explains git branch merge conflicts in migrations and provides safe `alembic merge heads` resolution.
- **Alembic Divergence**: Detects diverged database history and recommends non-destructive adoption.

---

## 🚢 CI/CD Integration

Use DBAnchor in GitHub Actions, GitLab CI, or Docker deployment pipelines:

```yaml
# .github/workflows/db-check.yml
name: Database Health Check
on: [push, pull_request]

jobs:
  db-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install dbanchor psycopg
      - run: dbx doctor --json
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          APP_ENV: staging
```

---

## 📄 License & Trademark

- **Code License**: Licensed under the **Apache License, Version 2.0**. See [LICENSE](LICENSE) for details.
- **Trademark Policy**: The **DBAnchor** and **dbx** names, logos, and brand guidelines are governed by our [Trademark Policy](TRADEMARK.md).
- **Security Policy**: For vulnerability reporting, see [SECURITY.md](SECURITY.md).
