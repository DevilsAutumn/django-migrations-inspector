# Django Migration Inspector

`django-migration-inspector` is an open source migration safety toolkit for Django.

The first implementation slice in this repository focuses on:

1. Loading Django migration graphs into a typed internal model.
2. Detecting merge nodes, multiple heads, root and leaf migrations, and dependency hotspots.
3. Analyzing both pending deploy plans and historical migration files with initial rule-driven risk scoring.
4. Rendering deterministic text, JSON, Mermaid, and Graphviz DOT reports.
5. Exposing a reusable `migration_inspect` Django management command.

Example usage:

```bash
python manage.py migration_inspect
python manage.py migration_inspect --risk
python manage.py migration_inspect --risk-history
python manage.py migration_inspect --rollback billing 0001_initial
python manage.py migration_inspect --format json
python manage.py migration_inspect --format mermaid
python manage.py migration_inspect --format dot
python manage.py migration_inspect --app analytics
```

To expose the management command, add `"django_migration_inspector"` to `INSTALLED_APPS`.

For hosted project documentation, this repository includes an MkDocs site that can be published on
GitHub Pages or Read the Docs.

Local docs commands:

```bash
python -m pip install '.[docs]'
mkdocs serve
mkdocs build --strict
```

Local quality commands:

```bash
ruff format .
ruff format --check .
ruff check .
mypy src tests
pytest -q
```
