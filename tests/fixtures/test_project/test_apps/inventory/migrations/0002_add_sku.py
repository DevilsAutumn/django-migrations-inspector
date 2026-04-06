"""Inventory branch migration adding a SKU."""

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (("inventory", "0001_initial"),)

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.AddField(
            model_name="widget",
            name="sku",
            field=models.CharField(default="", max_length=64),
        ),
    )
