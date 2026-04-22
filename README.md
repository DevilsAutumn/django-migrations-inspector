# Django Migrations Inspector

[![PyPI version](https://img.shields.io/pypi/v/django-migrations-inspector.svg)](https://pypi.org/project/django-migrations-inspector/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-migrations-inspector.svg)](https://pypi.org/project/django-migrations-inspector/)
[![Django support](https://img.shields.io/badge/Django-4.2%20--%206.0-0C4B33.svg)](https://github.com/DevilsAutumn/django-migrations-inspector/blob/main/docs/getting-started.md)
[![CI](https://github.com/DevilsAutumn/django-migrations-inspector/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/DevilsAutumn/django-migrations-inspector/actions/workflows/ci.yml)
[![Docs](https://github.com/DevilsAutumn/django-migrations-inspector/actions/workflows/docs.yml/badge.svg?branch=main)](https://devilsautumn.github.io/django-migrations-inspector/)
[![License](https://img.shields.io/github/license/DevilsAutumn/django-migrations-inspector.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/django-migrations-inspector?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/django-migrations-inspector)

`django-migrations-inspector` is an open source migration safety toolkit for Django.

Install the package from PyPI with:

```bash
python -m pip install django-migrations-inspector
```

Then add the Django app to `INSTALLED_APPS` with:

```python
INSTALLED_APPS = [
    # ...
    "django_migration_inspector",
]
```

It is designed around four practical Django questions:

1. `migration_inspect`: Is the migration graph healthy or messy?
2. `migration_inspect risk`: Are the pending migrations safe to deploy?
3. `migration_inspect audit`: Which migration files in this repo deserve attention?
4. `migration_inspect rollback APP TARGET`: If we need to reverse, what blocks us and what else gets touched?

How the commands work:

1. `migration_inspect` loads Django's migration graph and reports graph shape: heads, merge migrations, roots, leaves, and dependency hotspots. Add `--offline` to read migration files without opening a database connection.
2. `migration_inspect risk` asks Django for the pending forward migration plan, then checks those operations with safety rules for destructive schema changes, irreversible data code, raw SQL, unknown operations, and nested operations inside `SeparateDatabaseAndState`. This needs database state.
3. `migration_inspect audit` uses the same safety rules as `risk`, but scans the migration history instead of only pending migrations. Add `--offline` when you only want to review migration files on disk.
4. `migration_inspect rollback APP TARGET` asks Django for the reverse plan to reach `TARGET`. `TARGET` can be a full migration name, a unique prefix like `0008`, or `zero`. It checks reversibility, expected destructive reverse actions like dropping newly added tables or columns, and cross-app impact from migration dependencies, but it does not apply the rollback. This needs database state.

By default, `inspect`, `risk`, and `audit` ignore Django built-in apps and third-party apps.
Those reports focus on project apps that live inside your Django project tree rather than
everything installed in the environment.

`rollback` stays dependency-accurate instead of hiding external apps, because rollback safety can
depend on them.

The current implementation focuses on:

1. Loading Django migration graphs into a typed internal model.
2. Detecting merge nodes, multiple heads, root and leaf migrations, and dependency hotspots.
3. Analyzing both pending deploy plans and historical migration files with rule-driven risk scoring.
4. Simulating rollback plans with blockers, blast radius, cross-app impact, and reverse-step previews.
5. Rendering deterministic text, JSON, Mermaid, and Graphviz DOT reports.
6. Exposing a reusable `migration_inspect` Django management command.

Example usage:

```bash
python manage.py migration_inspect
python manage.py migration_inspect --offline
python manage.py migration_inspect --details
python manage.py migration_inspect risk
python manage.py migration_inspect risk --details
python manage.py migration_inspect audit
python manage.py migration_inspect audit --offline
python manage.py migration_inspect audit --details
python manage.py migration_inspect rollback billing 0001_initial
python manage.py migration_inspect rollback inventory zero
python manage.py migration_inspect rollback inventory zero --details
python manage.py migration_inspect rollback inventory 0001_initial --why-app catalog
python manage.py migration_inspect --json
python manage.py migration_inspect --format mermaid
python manage.py migration_inspect --format dot
python manage.py migration_inspect --app analytics
```

Replace `billing`, `inventory`, `catalog`, and `analytics` with app labels from your own Django project.

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
python -m pip install -e '.[dev,docs]'
ruff format .
ruff format --check .
ruff check .
mypy src tests
pytest -q
```
