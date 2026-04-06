"""Initial billing migration."""

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    initial = True

    dependencies: ClassVar[tuple[tuple[str, str], ...]] = ()

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("reference", models.CharField(max_length=32)),
            ],
        ),
    )
