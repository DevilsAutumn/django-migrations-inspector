"""Inventory merge migration resolving the split 0002 heads."""

from typing import ClassVar

from django.db import migrations
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (
        ("inventory", "0002_add_sku"),
        ("inventory", "0002_add_status"),
    )

    operations: ClassVar[tuple[Operation, ...]] = ()
