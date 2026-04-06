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

This gives you a stable summary of:

1. Root migrations.
2. Leaf migrations.
3. Merge migrations.
4. Apps with multiple heads.
5. Dependency hotspots.

## First risk report

To inspect the current forward migration plan:

```bash
python manage.py migration_inspect --risk
```

This reports:

1. Pending migration count.
2. Pending operation count.
3. Overall severity.
4. Rollback safety.
5. Rule-triggered findings with recommendations.

To audit migration files already on disk, even when nothing is pending:

```bash
python manage.py migration_inspect --risk-history
python manage.py migration_inspect --risk-history --app billing
```

## First rollback simulation

To preview a rollback path:

```bash
python manage.py migration_inspect --rollback billing 0001_initial
```

To preview unapplying an app entirely:

```bash
python manage.py migration_inspect --rollback billing zero
```

This reports:

1. Reverse migration order.
2. Irreversible blockers.
3. Cross-app rollback impact.
4. Merge-topology concerns.
5. Reverse operations in execution order.

## Machine-readable output

JSON output is designed for CI and tooling:

```bash
python manage.py migration_inspect --format json
```

## Visual output

To render the visible migration graph:

```bash
python manage.py migration_inspect --format mermaid
python manage.py migration_inspect --format dot
```

`mermaid` is a good fit for Markdown docs and pull requests. `dot` is a good fit for Graphviz and static graph tooling.
