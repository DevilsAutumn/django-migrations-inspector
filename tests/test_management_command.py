"""Integration tests for the management command."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import NoReturn

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.migrations.exceptions import NodeNotFoundError
from pytest import MonkeyPatch
from pytest_django.plugin import DjangoDbBlocker


def test_management_command_renders_json(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--format", "json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "graph_inspection"
    assert report["offline"] is False
    assert report["total_migrations"] == 11
    assert report["multiple_head_apps"][0]["app_label"] == "analytics"


def test_management_command_supports_app_filter(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--app", "inventory", stdout=output)

    rendered = output.getvalue()
    assert "Decision: CLEAR" in rendered
    assert "Scope: inventory" in rendered
    assert "Topology notes:" in rendered
    assert "inventory.0003_merge_0002_add_sku_0002_add_status" in rendered


def test_management_command_supports_offline_inspect(monkeypatch: MonkeyPatch) -> None:
    output = StringIO()

    def fail_database_connection(database_alias: str) -> NoReturn:
        raise AssertionError(f"Unexpected database connection for {database_alias}.")

    monkeypatch.setattr(
        "django_migration_inspector.django_adapter.loader.get_database_connection",
        fail_database_connection,
    )

    call_command("migration_inspect", "--offline", "--format", "json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "graph_inspection"
    assert report["offline"] is True
    assert report["total_migrations"] == 11


def test_management_command_rejects_ignored_app_filter(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        try:
            call_command(
                "migration_inspect",
                "--app",
                "django_migration_inspector",
                stdout=output,
            )
        except CommandError as error:
            assert "ignored because it is not a user project app" in str(error)
        else:
            raise AssertionError("Expected ignored app filter to be rejected.")


def test_management_command_rejects_unknown_database_alias_cleanly() -> None:
    output = StringIO()

    try:
        call_command("migration_inspect", "--database", "missing", stdout=output)
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected unknown database alias to fail.")

    assert "Unknown database alias 'missing'" in error_message
    assert "Traceback" not in error_message


def test_management_command_rejects_malformed_database_env_cleanly(
    monkeypatch: MonkeyPatch,
) -> None:
    output = StringIO()

    def fail_dotenv_hydration(connection: object, *, database_alias: str) -> NoReturn:
        del connection, database_alias
        raise ValueError("Port could not be cast to integer value as 'not-a-port'")

    monkeypatch.setattr(
        "django_migration_inspector.django_adapter.loader._hydrate_connection_settings_from_dotenv",
        fail_dotenv_hydration,
    )

    try:
        call_command("migration_inspect", stdout=output)
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected malformed database environment to fail.")

    assert "Could not parse database configuration for alias 'default'" in error_message
    assert "not-a-port" in error_message
    assert "Traceback" not in error_message


def test_management_command_rejects_invalid_output_path_cleanly(tmp_path: Path) -> None:
    output = StringIO()
    output_path = tmp_path / "missing-parent" / "report.txt"

    try:
        call_command(
            "migration_inspect",
            "--offline",
            "--output",
            str(output_path),
            stdout=output,
        )
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected invalid output path to fail.")

    assert "Could not write migration report" in error_message
    assert str(output_path) in error_message
    assert "Traceback" not in error_message


def test_management_command_rejects_broken_migration_graph_cleanly(
    monkeypatch: MonkeyPatch,
) -> None:
    output = StringIO()

    class BrokenGraphService:
        def inspect_graph(self, config: object) -> NoReturn:
            del config
            raise NodeNotFoundError(
                "Migration inventory.0002_bad dependencies reference missing parent.",
                ("inventory", "0002_bad"),
            )

    monkeypatch.setattr(
        "django_migration_inspector.management.commands.migration_inspect."
        "build_default_inspect_service",
        lambda: BrokenGraphService(),
    )

    try:
        call_command("migration_inspect", stdout=output)
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected broken migration graph to fail.")

    assert "could not load a consistent migration graph" in error_message
    assert "0002_bad" in error_message
    assert "Traceback" not in error_message


def test_management_command_rejects_broken_migration_import_cleanly(
    monkeypatch: MonkeyPatch,
) -> None:
    output = StringIO()

    class BrokenImportService:
        def inspect_graph(self, config: object) -> NoReturn:
            del config
            raise ModuleNotFoundError("No module named 'legacy_payments'")

    monkeypatch.setattr(
        "django_migration_inspector.management.commands.migration_inspect."
        "build_default_inspect_service",
        lambda: BrokenImportService(),
    )

    try:
        call_command("migration_inspect", stdout=output)
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected broken migration import to fail.")

    assert "could not import one of the project or migration modules" in error_message
    assert "legacy_payments" in error_message
    assert "Traceback" not in error_message


def test_management_command_rejects_migration_file_read_error_cleanly(
    monkeypatch: MonkeyPatch,
) -> None:
    output = StringIO()

    class BrokenFileService:
        def inspect_graph(self, config: object) -> NoReturn:
            del config
            raise PermissionError("permission denied: inventory/migrations/0001_initial.py")

    monkeypatch.setattr(
        "django_migration_inspector.management.commands.migration_inspect."
        "build_default_inspect_service",
        lambda: BrokenFileService(),
    )

    try:
        call_command("migration_inspect", stdout=output)
    except CommandError as error:
        error_message = str(error)
    else:
        raise AssertionError("Expected migration file read error to fail.")

    assert "could not read one of the project or migration files" in error_message
    assert "0001_initial.py" in error_message
    assert "Traceback" not in error_message
