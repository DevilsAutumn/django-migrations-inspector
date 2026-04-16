# Rollback Simulation

Rollback simulation helps answer a question teams usually face under pressure:

> If we need to reverse this deploy, what exactly gets unapplied and what will block us?

## Basic usage

Simulate rollback to a specific migration:

```bash
python manage.py migration_inspect rollback billing 0001_initial
python manage.py migration_inspect rollback billing 0001
```

Unique migration prefixes are accepted, so `0001` resolves to `0001_initial` when there is only
one matching migration in that app. Ambiguous prefixes still fail with an error.

Simulate unapplying an app back to zero:

```bash
python manage.py migration_inspect rollback billing zero
```

JSON output is also supported:

```bash
python manage.py migration_inspect rollback billing 0001_initial --json
```

For larger projects, the text output is summary-first by default:

```bash
python manage.py migration_inspect rollback inventory zero
python manage.py migration_inspect rollback inventory zero --details
python manage.py migration_inspect rollback inventory zero --show-operations
python manage.py migration_inspect rollback inventory 0001_initial --why-app catalog
python manage.py migration_inspect rollback inventory zero --output inventory-rollback.txt
```


Unlike `inspect`, `risk`, and `audit`, rollback does not hide dependency-driven external apps.
If another app would really be touched during reversal, it is kept in the rollback report.

Rollback simulation only reads Django's migration plan. It does not apply or fake-unapply any
migration.

## What the report includes

The simulator currently reports:

1. Whether rollback is blocked, high risk, or clear.
2. The rollback blast radius across steps and apps.
3. Irreversible blockers.
4. Expected but destructive reverse actions, like dropping tables or columns added after the target migration.
5. Data-loss reversals such as restoring dropped fields or deleted tables without restoring data.
6. Cross-app impact caused by dependencies.
7. Merge-migration warnings.
8. App-level impact summaries.
9. Reverse operations in execution order when requested.

## Output modes

The default text output is designed for large rollback plans:

1. Decision and blast radius
2. Summary of blockers, expected destructive reverse actions, data-loss reversals, and dependency reach
3. Why other apps are included
4. App impact summary
5. Top risky migrations

Use `--details` to include the full step list and concern list.
Use `--show-operations` to include reverse operations under each step.
Use `--why-app APP_LABEL` to focus on one dependency chain.

## Current blocker behavior

Rollback is marked as not possible when the reverse path includes irreversible operations, such as:

1. Irreversible `RunPython`
2. Irreversible `RunSQL`
3. Any custom operation marked non-reversible by Django

If these operations are nested inside `SeparateDatabaseAndState`, the simulator still checks them.
It does not trust the wrapper alone.

## Current concerns surfaced

The simulator also flags non-blocking but important concerns, including:

1. Removing tables or columns that were added after the rollback target
2. Recreating schema after dropped data
3. Raw SQL in the reverse path
4. Cross-app dependency impact
5. Merge-topology complexity

## Current scope

Future work can improve:

1. Lock and downtime heuristics for reverse operations
2. Better handling for fake-applied and drifted environments
3. More production-specific recovery guidance
