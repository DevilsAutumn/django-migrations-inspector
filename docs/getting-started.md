# Getting Started

## Requirements

The package currently targets:

1. Python 3.10+
2. Django 4.2 through 6.x

## Installation

Install the package from PyPI:

```bash
python -m pip install django-migrations-inspector
```

Then include the Django app in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_migration_inspector",
]
```

For development:

```bash
python -m pip install uv
uv sync --python 3.12 --all-groups
```

## First command

Run the graph inspection command from your Django project:

```bash
python manage.py migration_inspect
```

If the database is not set up yet, scan migration files only:

```bash
python manage.py migration_inspect --offline
```

By default, the command ignores Django built-in apps and third-party apps so the report focuses on
your project code.

This gives you a stable summary of:

1. Whether the visible graph needs attention.
2. Which apps have multiple heads.
3. Which merge migrations exist.
4. Which nodes are dependency hotspots.

Use `--details` when you want the root and leaf migration lists too:

```bash
python manage.py migration_inspect --details
```

## First risk report

To inspect the current forward migration plan:

```bash
python manage.py migration_inspect risk
```

This reports:

1. Whether rollback is blocked.
2. Which pending migrations are destructive.
3. Which migrations need manual review.
4. Which apps need attention first.

Use `--details` for the full per-operation finding list:

```bash
python manage.py migration_inspect risk --details
```

Detailed text output separates exact findings from guidance. The finding list tells you which
migration operation was flagged; the guidance section prints each repeated recommendation once.

To audit migration files already on disk, even when nothing is pending:

```bash
python manage.py migration_inspect audit
python manage.py migration_inspect audit --offline
python manage.py migration_inspect audit --app billing
python manage.py migration_inspect audit --details
```

## First rollback simulation

To preview a rollback path:

```bash
python manage.py migration_inspect rollback billing 0001_initial
```

To preview unapplying an app entirely:

```bash
python manage.py migration_inspect rollback billing zero
```

This reports:

1. Whether rollback is blocked, risky, or clear.
2. The rollback blast radius across steps and apps.
3. Which migrations will remove tables or columns added after the target migration.
4. Which migrations restore schema shape without restoring deleted data.
5. Why other apps are included.
6. Grouped guidance for the blockers and concerns found.

Use `--details` or `--show-operations` when you need the full rollback plan.
Rollback details follow the same evidence-first shape: the step and concern lists stay factual,
while repeated recovery advice is grouped under guidance.

## Machine-readable output

JSON output is designed for CI and tooling:

```bash
python manage.py migration_inspect --json
```

## Visual output

To render the visible migration graph:

```bash
python manage.py migration_inspect --format mermaid
python manage.py migration_inspect --format dot
```

`mermaid` is a good fit for Markdown docs and pull requests. `dot` is a good fit for Graphviz and static graph tooling.
