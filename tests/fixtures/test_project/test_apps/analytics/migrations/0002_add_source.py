"""Analytics branch migration adding a source field."""

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (("analytics", "0001_initial"),)

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.AddField(
            model_name="event",
            name="source",
            field=models.CharField(default="web", max_length=32),
        ),
    )
