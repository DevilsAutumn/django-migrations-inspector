# Development

## Local environment

The repository uses `uv` for maintainer and contributor workflows. Package users can still install
the published library with `pip`; `uv` is only the internal development tool.

Example:

```bash
python -m pip install uv
uv sync --python 3.12 --all-groups
```

## Quality commands

Run all core checks before merging:

```bash
uv run ruff format .
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest -q
uv run mkdocs build --strict
```

The repository also includes a GitHub Actions workflow at `.github/workflows/ci.yml` that
enforces the same checks on pushes and pull requests.

## Release workflow

Build and validate release artifacts locally with:

```bash
uv sync --no-default-groups --group release
uv build
uv run twine check dist/*
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
uv sync --no-default-groups --group docs
uv run mkdocs serve
uv run mkdocs build --strict
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
