"""Integration tests for the management command."""

from __future__ import annotations

import json
from io import StringIO
from typing import NoReturn

from django.core.management import call_command
from django.core.management.base import CommandError
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
    assert "Scope: inventory" in rendered
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
