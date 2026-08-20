# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability or security-related issue in DBAnchor:

1. **Do not create a public GitHub issue.**
2. Send a detailed report to **security@dbanchor.dev**.
3. Include reproduction steps, environment details, and affected version.
4. We will acknowledge receipt within 48 hours and provide a timeline for triage and resolution.

---

## Core Security Guarantees

- **Zero Secret Leakage**: Database passwords, connection parameters, and sensitive credentials are automatically redacted across all CLI output, JSON reports, loggers, and stack traces.
- **SQL Injection Prevention**: Dynamic queries are prohibited. All live schema inspection relies strictly on parameterized metadata queries and SQLAlchemy inspection primitives.
- **Destructive Execution Protection**: Production environments require manual validation before executing potentially data-destructive operations.
