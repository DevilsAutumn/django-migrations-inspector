"""Integration tests for the management command."""

from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from pytest_django.plugin import DjangoDbBlocker


def test_management_command_renders_json(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--format", "json", stdout=output)

    report = json.loads(output.getvalue())
    assert report["report_type"] == "graph_inspection"
    assert report["total_migrations"] == 11
    assert report["multiple_head_apps"][0]["app_label"] == "analytics"


def test_management_command_supports_app_filter(django_db_blocker: DjangoDbBlocker) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        call_command("migration_inspect", "--app", "inventory", stdout=output)

    rendered = output.getvalue()
    assert "Scope: inventory" in rendered
    assert "inventory.0003_merge_0002_add_sku_0002_add_status" in rendered
