# Rollback Simulation

Rollback simulation helps answer a question teams usually face under pressure:

> If we need to reverse this deploy, what exactly gets unapplied and what will block us?

## Basic usage

Simulate rollback to a specific migration:

```bash
python manage.py migration_inspect --rollback billing 0001_initial
```

Simulate unapplying an app back to zero:

```bash
python manage.py migration_inspect --rollback billing zero
```

JSON output is also supported:

```bash
python manage.py migration_inspect --rollback billing 0001_initial --format json
```

## What the report includes

The simulator currently reports:

1. Reverse migration order.
2. Whether rollback is possible.
3. Whether rollback is operationally safe.
4. Irreversible blockers.
5. Cross-app impact caused by dependencies.
6. Merge-migration warnings.
7. Reverse operations in execution order.

## Current blocker behavior

Rollback is marked as not possible when the reverse path includes irreversible operations, such as:

1. Irreversible `RunPython`
2. Irreversible `RunSQL`
3. Any custom operation marked non-reversible by Django

## Current concerns surfaced

The simulator also flags non-blocking but important concerns, including:

1. Recreating schema after dropped data
2. Raw SQL in the reverse path
3. Cross-app dependency impact
4. Merge-topology complexity

## Current scope

This is the first rollback slice. Future work can improve:

1. Lock and downtime heuristics for reverse operations
2. Detailed dependency reasoning per app
3. Better handling for fake-applied and drifted environments
