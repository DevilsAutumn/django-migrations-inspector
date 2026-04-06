"""Analytics branch migration adding a payload field."""

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (("analytics", "0001_initial"),)

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.AddField(
            model_name="event",
            name="payload",
            field=models.JSONField(default=dict),
        ),
    )
