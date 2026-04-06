# Development

## Local environment

The repository works best in a Python 3.12 virtual environment during development.

Example:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Quality commands

Run all core checks before merging:

```bash
ruff check .
mypy src tests
pytest -q
```

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
   Pure graph intelligence logic.
4. `renderers/`
   Text, JSON, Mermaid, and DOT outputs.
5. `services/`
   Thin orchestration between providers and analyzers.
6. `management/commands/`
   Django CLI entry points.
