# Django Migration Inspector

`django-migration-inspector` is an open source migration safety toolkit for Django.

It is designed around four practical Django questions:

1. `migration_inspect`: Is the migration graph healthy or messy?
2. `migration_inspect risk`: Are the pending migrations safe to deploy?
3. `migration_inspect audit`: Which migration files in this repo deserve attention?
4. `migration_inspect rollback APP TARGET`: If we need to reverse, what blocks us and what else gets touched?

By default, `inspect`, `risk`, and `audit` ignore Django built-in apps and third-party apps.
Those reports focus on project apps that live inside your Django project tree rather than
everything installed in the environment.

`rollback` stays dependency-accurate instead of hiding external apps, because rollback safety can
depend on them.

The first implementation slice in this repository focuses on:

1. Loading Django migration graphs into a typed internal model.
2. Detecting merge nodes, multiple heads, root and leaf migrations, and dependency hotspots.
3. Analyzing both pending deploy plans and historical migration files with initial rule-driven risk scoring.
4. Rendering deterministic text, JSON, Mermaid, and Graphviz DOT reports.
5. Exposing a reusable `migration_inspect` Django management command.

Example usage:

```bash
python manage.py migration_inspect
python manage.py migration_inspect --details
python manage.py migration_inspect risk
python manage.py migration_inspect risk --details
python manage.py migration_inspect audit
python manage.py migration_inspect audit --details
python manage.py migration_inspect rollback billing 0001_initial
python manage.py migration_inspect rollback users zero
python manage.py migration_inspect rollback users zero --details
python manage.py migration_inspect rollback users zero --why-app trips
python manage.py migration_inspect --json
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
