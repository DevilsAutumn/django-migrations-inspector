# CLI Reference

## `migration_inspect`

Inspect the Django migration graph and emit a stable report.

### Basic usage

```bash
python manage.py migration_inspect
python manage.py migration_inspect --risk
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

## Output expectations

### `text`

Human-readable local summary.

### `json`

Deterministic structured output for CI and downstream tooling.

### `mermaid`

Local-first visual graph that works well in Markdown-aware tools.

### `dot`

Graphviz DOT output for richer graph rendering pipelines.
