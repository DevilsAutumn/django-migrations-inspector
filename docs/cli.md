# CLI Reference

## `migration_inspect`

Inspect the Django migration graph and emit a stable report.

### Basic usage

```bash
python manage.py migration_inspect
python manage.py migration_inspect --risk
python manage.py migration_inspect --risk-history
python manage.py migration_inspect --rollback billing 0001_initial
python manage.py migration_inspect --rollback users zero --why-app trips
```

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

#### `--database`

Choose the Django database alias used when loading migration state:

```bash
python manage.py migration_inspect --database default
```

#### `--output`

Write the rendered report to a file instead of stdout:

```bash
python manage.py migration_inspect --rollback users zero --output rollback-summary.txt
python manage.py migration_inspect --rollback users zero --format json --output rollback.json
```

#### `--pager`

Choose whether long text output should open in a pager:

```bash
python manage.py migration_inspect --rollback users zero --pager auto
python manage.py migration_inspect --rollback users zero --pager on
python manage.py migration_inspect --rollback users zero --pager off
```

#### `--risk`

Analyze the pending forward migration plan rather than rendering the graph summary:

```bash
python manage.py migration_inspect --risk
python manage.py migration_inspect --risk --format json
python manage.py migration_inspect --risk --app billing
```

`--risk` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

When there are no pending migrations, `--risk` now prints a note explaining that it only checked unapplied forward steps.
Use `--risk-history` to audit the migrations already present on disk.

#### `--risk-history`

Audit all visible migrations on disk rather than only the pending forward plan:

```bash
python manage.py migration_inspect --risk-history
python manage.py migration_inspect --risk-history --format json
python manage.py migration_inspect --risk-history --app billing
```

`--risk-history` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

#### `--rollback APP_LABEL MIGRATION_NAME`

Simulate rollback to a requested migration target:

```bash
python manage.py migration_inspect --rollback billing 0001_initial
python manage.py migration_inspect --rollback billing zero
python manage.py migration_inspect --rollback billing 0001_initial --format json
python manage.py migration_inspect --rollback users zero --verbose
python manage.py migration_inspect --rollback users zero --show-operations
python manage.py migration_inspect --rollback users zero --why-app trips
```

`--rollback` currently supports:

1. `text`
2. `json`

It does not currently support `mermaid` or `dot`.

Text rollback output is summary-first by default, so large rollback plans do not flood the terminal.
Use the following flags to expand detail only when you need it:

#### `--verbose`

For text rollback output, include the per-step rollback list and the full concern list:

```bash
python manage.py migration_inspect --rollback users zero --verbose
```

#### `--show-operations`

For text rollback output, include reverse operations for each rollback step.
This implies the same detailed mode as `--verbose`:

```bash
python manage.py migration_inspect --rollback users zero --show-operations
```

#### `--why-app APP_LABEL`

For text rollback output, explain why one cross-app dependency chain is part of the rollback plan:

```bash
python manage.py migration_inspect --rollback users zero --why-app trips
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
