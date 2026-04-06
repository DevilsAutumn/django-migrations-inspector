"""Billing migration removing a populated reference field."""

from typing import ClassVar

from django.db import migrations
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (("billing", "0001_initial"),)

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.RemoveField(
            model_name="invoice",
            name="reference",
        ),
    )
