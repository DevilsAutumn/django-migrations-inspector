"""Integration tests for rollback simulation and command output."""

from __future__ import annotations

import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.db.migrations.recorder import MigrationRecorder
from pytest_django.plugin import DjangoDbBlocker

from django_migration_inspector.config import RollbackConfig
from django_migration_inspector.domain.enums import RiskSeverity
from django_migration_inspector.services import build_default_rollback_service


def _set_applied_migrations(*migration_keys: tuple[str, str]) -> None:
    connection = connections["default"]
    recorder = MigrationRecorder(connection)
    recorder.ensure_schema()
    recorder.Migration.objects.using(connection.alias).all().delete()
    for app_label, migration_name in migration_keys:
        recorder.record_applied(app_label, migration_name)


def test_rollback_service_detects_irreversible_blocker(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_rollback_service()

    with django_db_blocker.unblock():
        _set_applied_migrations(
            ("billing", "0001_initial"),
            ("billing", "0002_remove_reference"),
            ("billing", "0003_irreversible_cleanup"),
        )
        report = service.inspect_rollback(
            RollbackConfig(target_app_label="billing", target_migration_name="0001_initial")
        )

    assert report.step_count == 2
    assert report.overall_severity is RiskSeverity.CRITICAL
    assert report.rollback_possible is False
    assert report.rollback_safe is False
    assert report.blockers[0].migration.identifier == "billing.0003_irreversible_cleanup"
    assert "data_loss_reversal" in {concern.category for concern in report.concerns}


def test_rollback_service_surfaces_cross_app_impact(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_rollback_service()

    with django_db_blocker.unblock():
        _set_applied_migrations(
            ("inventory", "0001_initial"),
            ("inventory", "0002_add_sku"),
            ("inventory", "0002_add_status"),
            ("inventory", "0003_merge_0002_add_sku_0002_add_status"),
            ("catalog", "0001_initial"),
        )
        report = service.inspect_rollback(
            RollbackConfig(target_app_label="inventory", target_migration_name="0001_initial")
        )

    assert report.rollback_possible is True
    assert "catalog" in report.plan.affected_app_labels
    assert any(concern.category == "cross_app_impact" for concern in report.concerns)
    merge_flags = {step.key.identifier: step.is_merge for step in report.plan.steps}
    assert merge_flags["inventory.0003_merge_0002_add_sku_0002_add_status"] is True
    assert merge_flags["inventory.0002_add_sku"] is False
    assert merge_flags["inventory.0002_add_status"] is False


def test_rollback_service_uses_reverse_operation_labels(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    service = build_default_rollback_service()

    with django_db_blocker.unblock():
        _set_applied_migrations(
            ("inventory", "0001_initial"),
            ("inventory", "0002_add_sku"),
            ("inventory", "0002_add_status"),
            ("inventory", "0003_merge_0002_add_sku_0002_add_status"),
        )
        report = service.inspect_rollback(
            RollbackConfig(target_app_label="inventory", target_migration_name="zero")
        )

    operations_by_step = {
        step.key.identifier: tuple(operation.name for operation in step.reverse_operations)
        for step in report.plan.steps
    }
    descriptions_by_step = {
        step.key.identifier: tuple(operation.description for operation in step.reverse_operations)
        for step in report.plan.steps
    }

    assert operations_by_step["inventory.0002_add_sku"] == ("RemoveField",)
    assert descriptions_by_step["inventory.0002_add_sku"] == ("Remove field sku from widget",)
    assert operations_by_step["inventory.0001_initial"] == ("DeleteModel",)
    assert descriptions_by_step["inventory.0001_initial"] == ("Delete model Widget",)


def test_management_command_renders_rollback_json(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        _set_applied_migrations(
            ("billing", "0001_initial"),
            ("billing", "0002_remove_reference"),
            ("billing", "0003_irreversible_cleanup"),
        )
        call_command(
            "migration_inspect",
            "--rollback",
            "billing",
            "0001_initial",
            "--format",
            "json",
            stdout=output,
        )

    report = json.loads(output.getvalue())
    assert report["report_type"] == "rollback_simulation"
    assert report["rollback_possible"] is False
    assert report["overall_severity"] == "critical"
    assert any(blocker["operation_name"] == "RunPython" for blocker in report["blockers"])


def test_management_command_renders_rollback_text(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        _set_applied_migrations(
            ("inventory", "0001_initial"),
            ("inventory", "0002_add_sku"),
            ("inventory", "0002_add_status"),
            ("inventory", "0003_merge_0002_add_sku_0002_add_status"),
            ("catalog", "0001_initial"),
        )
        call_command(
            "migration_inspect",
            "--rollback",
            "inventory",
            "0001_initial",
            stdout=output,
        )

    rendered = output.getvalue()
    assert "Target: inventory.0001_initial" in rendered
    assert "Affected apps: catalog, inventory" in rendered
    assert "inventory.0003_merge_0002_add_sku_0002_add_status [merge]" in rendered
    assert "RemoveField: Remove field sku from widget" in rendered


def test_management_command_rejects_visual_rollback_format(
    django_db_blocker: DjangoDbBlocker,
) -> None:
    output = StringIO()

    with django_db_blocker.unblock():
        try:
            call_command(
                "migration_inspect",
                "--rollback",
                "billing",
                "0001_initial",
                "--format",
                "dot",
                stdout=output,
            )
        except CommandError as error:
            assert "supports only text and json" in str(error)
        else:
            raise AssertionError("Expected rollback mode with DOT output to fail.")
