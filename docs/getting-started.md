# Getting Started

## Requirements

The package currently targets:

1. Python 3.10+
2. Django 4.2 through 5.x

## Installation

Add the package to your Django project and include the app in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_migration_inspector",
]
```

Install from a local checkout:

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e '.[dev]'
```

## First command

Run the graph inspection command from your Django project:

```bash
python manage.py migration_inspect
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

To audit migration files already on disk, even when nothing is pending:

```bash
python manage.py migration_inspect audit
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
3. Which migrations lose data on reversal.
4. Why other apps are included.

Use `--details` or `--show-operations` when you need the full rollback plan.

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
