# CLI Reference

## `migration_inspect`

Inspect the Django migration graph and emit a stable report.

The command is designed around four different questions:

1. `inspect`: Is the graph easy to reason about?
2. `risk`: Are pending migrations safe to deploy?
3. `audit`: Which migrations on disk need human review?
4. `rollback`: If I reverse, what blocks me and what else breaks?

By default, `inspect`, `risk`, and `audit` ignore Django built-in apps and third-party apps.
Those modes focus on project apps detected from the Django project roots instead of everything in
`site-packages`.

`rollback` is different: it still surfaces non-project apps when dependency chains make them part
of the real rollback path.

### Basic usage

```bash
python manage.py migration_inspect
python manage.py migration_inspect --offline
python manage.py migration_inspect risk
python manage.py migration_inspect audit
python manage.py migration_inspect audit --offline
python manage.py migration_inspect rollback billing 0001_initial
python manage.py migration_inspect rollback inventory 0001_initial --why-app catalog
```

The command now supports a simpler subcommand style:

1. `inspect`
2. `risk`
3. `audit`
4. `rollback`

### Options

#### `--format`

Supported values:

1. `text`
2. `json`
3. `mermaid`
4. `dot`

Examples:

```bash
python manage.py migration_inspect --format text
python manage.py migration_inspect --format json
python manage.py migration_inspect --format mermaid
python manage.py migration_inspect --format dot
```

#### `--app`

Limit the report to a single Django app label:

```bash
python manage.py migration_inspect --app inventory
```

This is useful when:

1. A single app has branching migrations.
2. You want a smaller graph for documentation or review.
3. You want to focus on one release area.

`--app` works with `inspect`, `risk`, and `audit`. Rollback mode takes the target app as a
positional argument, so `--app` is rejected there.

#### `--database`

Choose the Django database alias used when loading migration state:

```bash
python manage.py migration_inspect --database default
```

#### `--offline`

Load migration files without connecting to the configured database:

```bash
python manage.py migration_inspect --offline
python manage.py migration_inspect audit --offline
python manage.py migration_inspect --offline --format mermaid
```

`--offline` is supported for `inspect` and `audit`. It is useful when you want to scan a large
project before setting up Postgres, MySQL, or local credentials.

`risk` and `rollback` still need a real database connection because they depend on the current
applied migration state in the `django_migrations` table.

#### `--output`

Write the rendered report to a file instead of stdout:

```bash
python manage.py migration_inspect rollback inventory zero --output rollback-summary.txt
python manage.py migration_inspect rollback inventory zero --json --output rollback.json
```

#### `risk`

Analyze the pending forward migration plan rather than rendering the graph summary:

```bash
python manage.py migration_inspect risk
python manage.py migration_inspect risk --json
python manage.py migration_inspect risk --app billing
```

`risk` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

`risk` cannot run with `--offline` because pending migrations depend on the current database state.

The default text output is summary-first:

1. Decision: `CLEAR`, `REVIEW REQUIRED`, or `ROLLBACK BLOCKED`
2. Counts for rollback blockers, destructive migrations, and review-needed migrations
3. Apps needing attention
4. Top migrations to look at first

Use `--details` for the full per-operation review list.

When there are no pending migrations, `risk` prints a note explaining that it only checked unapplied forward steps.
Use `audit` to inspect the migrations already present on disk.

#### `audit`

Audit all visible migrations on disk rather than only the pending forward plan:

```bash
python manage.py migration_inspect audit
python manage.py migration_inspect audit --json
python manage.py migration_inspect audit --offline
python manage.py migration_inspect audit --app billing
```

`audit` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

The default text output is summary-first:

1. Decision: `CLEAR`, `REVIEW REQUIRED`, or `IRREVERSIBLE FOUND`
2. Counts for irreversible, destructive, and review-needed migrations
3. Risky migration count by app
4. Top historical migrations that deserve review

Use `--details` for the full finding list.

Use `audit --offline` when you want a file-only review of a project whose database is not set up.

#### `rollback APP_LABEL MIGRATION_NAME`

Simulate rollback to a requested migration target:

```bash
python manage.py migration_inspect rollback billing 0001_initial
python manage.py migration_inspect rollback billing 0001
python manage.py migration_inspect rollback billing zero
python manage.py migration_inspect rollback billing 0001_initial --json
python manage.py migration_inspect rollback inventory zero --details
python manage.py migration_inspect rollback inventory zero --show-operations
python manage.py migration_inspect rollback inventory 0001_initial --why-app catalog
```

Rollback targets accept unique prefixes within the selected app, so `0001` can resolve to
`0001_initial`. Ambiguous prefixes are rejected with a clear error message.

`rollback` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

Text rollback output is summary-first by default, so large rollback plans do not flood the terminal.
Use the following flags to expand detail only when you need it:

Rollback cannot run with `--offline` because the reverse plan depends on applied migrations in the
database.

#### `--details`

For text output, include the full detailed listing for the selected mode:

```bash
python manage.py migration_inspect --details
python manage.py migration_inspect risk --details
python manage.py migration_inspect audit --details
python manage.py migration_inspect rollback inventory zero --details
```

#### `--show-operations`

For text rollback output, include reverse operations for each rollback step.
This implies the same detailed mode as `--details`:

```bash
python manage.py migration_inspect rollback inventory zero --show-operations
```

#### `--why-app APP_LABEL`

For text rollback output, explain why one cross-app dependency chain is part of the rollback plan:

```bash
python manage.py migration_inspect rollback inventory 0001_initial --why-app catalog
```

## Output expectations

### `text`

Human-readable local summary.

### `json`

Deterministic structured output for CI and downstream tooling.

### `mermaid`

Local-first visual graph that works well in Markdown-aware tools.

### `dot`

Graphviz DOT output for richer graph rendering pipelines.
