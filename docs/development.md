# Development

## Local environment

The repository works best in a Python 3.12 virtual environment during development.

Example:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev,docs]'
```

## Quality commands

Run all core checks before merging:

```bash
ruff format .
ruff format --check .
ruff check .
mypy src tests
pytest -q
mkdocs build --strict
```

The repository also includes a GitHub Actions workflow at `.github/workflows/ci.yml` that
enforces the same checks on pushes and pull requests.

## Release workflow

Build and validate release artifacts locally with:

```bash
python -m pip install -e '.[release]'
python -m build
python -m twine check dist/*
```

The repository also includes `.github/workflows/release.yml` for Trusted Publishing.

Recommended release flow:

1. Update `version` in `pyproject.toml` and `src/django_migration_inspector/__about__.py`.
2. Run the local release checks.
3. Trigger the `release` workflow with `testpypi` selected.
4. Configure GitHub environments named `testpypi` and `pypi` as Trusted Publishers in TestPyPI and PyPI.
5. Push a version tag such as `v0.1.0` to publish to PyPI.

## Documentation workflow

Install docs dependencies and build locally:

```bash
python -m pip install -e '.[docs]'
mkdocs serve
mkdocs build --strict
```

## Code style rules

The package is intentionally strict:

1. Typed public interfaces.
2. `mypy --strict`.
3. Deterministic render outputs.
4. Django internals isolated in adapter modules.
5. Pure analysis layers wherever possible.

## Architecture outline

The current implementation is split into:

1. `django_adapter/`
   Django-specific graph loading and operation normalization.
2. `domain/`
   Immutable typed models and report contracts.
3. `analyzers/`
   Pure graph intelligence, risk, and rollback logic.
4. `renderers/`
   Text, JSON, Mermaid, DOT, risk-report, and rollback-report outputs.
5. `services/`
   Thin orchestration between providers and analyzers.
6. `management/commands/`
   Django CLI entry points.
7. `risk_rules/`
   Built-in rule modules for destructive, custom, and data-migration checks.
