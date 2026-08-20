# Contributing to DBAnchor

We welcome contributions to DBAnchor! Whether you are fixing bugs, improving documentation, adding diagnostics rules, or enhancing CLI capabilities, your help is appreciated.

Official website: **https://dbanchor.calgebrity.com/**

---


## Code of Conduct

All contributors are expected to adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/calgebrity-cmyk/DBAnchor.git
   cd dbanchor
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -e ".[dev,all-drivers]"
   ```

4. **Run the test suite**:
   ```bash
   pytest
   ```

5. **Run linting & typing checks**:
   ```bash
   ruff check .
   mypy src/dbanchor
   ```

---

## Architectural Guidelines

- **Never perform automatic destructive changes**: Destructive actions (`DROP TABLE`, `DROP COLUMN`, etc.) must always require explicit confirmation.
- **Always redact credentials**: Passwords and connection secrets must never appear in CLI logs, tables, JSON exports, or unhandled exceptions.
- **Deterministic first**: Prioritize clean, reliable diagnostic rules over flaky heuristics.
- **Preserve existing workflows**: Never force an opinionated project reorganization onto existing developers.

---

## Submitting Pull Requests

1. Create a descriptive branch: `git checkout -b fix/auth-url-encoding-diagnostic`.
2. Write tests covering your changes.
3. Ensure all tests and linters pass (`pytest`, `ruff check .`, `mypy src/dbanchor`).
4. Submit a Pull Request targeting the `main` branch with a clear summary and verification steps.
