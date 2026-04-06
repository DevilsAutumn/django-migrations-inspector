"""Billing migration with irreversible custom data logic."""

from typing import ClassVar

from django.db import migrations
from django.db.migrations.operations.base import Operation


def cleanup_invoices(apps: object, schema_editor: object) -> None:
    """Placeholder irreversible cleanup used for risk-analysis tests."""

    del apps
    del schema_editor


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (("billing", "0002_remove_reference"),)

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.RunPython(cleanup_invoices),
    )
