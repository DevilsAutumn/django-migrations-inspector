"""Unit tests for rollback adapter helpers."""

from __future__ import annotations

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.migration import Migration
from django.db.migrations.operations.base import Operation

from django_migration_inspector.django_adapter.operations import (
    build_rollback_operation_descriptor,
)
from django_migration_inspector.django_adapter.rollback import _is_merge_migration


def test_build_rollback_operation_descriptor_describes_reverse_add_field() -> None:
    operation: Operation = migrations.AddField(
        model_name="widget",
        name="sku",
        field=models.CharField(default="", max_length=64),
    )

    descriptor = build_rollback_operation_descriptor(operation=operation, index=0)

    assert descriptor.name == "RemoveField"
    assert descriptor.source_name == "AddField"
    assert descriptor.description == "Remove field sku from widget"


def test_build_rollback_operation_descriptor_describes_reverse_create_model() -> None:
    operation: Operation = migrations.CreateModel(
        name="Widget",
        fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
        ],
    )

    descriptor = build_rollback_operation_descriptor(operation=operation, index=0)

    assert descriptor.name == "DeleteModel"
    assert descriptor.source_name == "CreateModel"
    assert descriptor.description == "Delete model Widget"


def test_is_merge_migration_requires_multiple_same_app_parents() -> None:
    class NonMergeMigration(Migration):
        dependencies: ClassVar[list[tuple[str, str]]] = [
            ("billing", "0001_initial"),
            ("auth", "0012_alter_user_first_name_max_length"),
        ]

    class MergeMigration(Migration):
        dependencies: ClassVar[list[tuple[str, str]]] = [
            ("billing", "0002_left"),
            ("billing", "0002_right"),
            ("auth", "0012_alter_user_first_name_max_length"),
        ]

    non_merge = NonMergeMigration(name="0002_example", app_label="billing")
    merge = MergeMigration(name="0003_merge_example", app_label="billing")

    assert _is_merge_migration(non_merge) is False
    assert _is_merge_migration(merge) is True
