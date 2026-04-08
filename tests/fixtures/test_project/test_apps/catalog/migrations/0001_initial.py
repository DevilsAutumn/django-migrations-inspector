"""Initial catalog migration with a cross-app dependency."""

from typing import ClassVar

from django.db import migrations, models
from django.db.migrations.operations.base import Operation


class Migration(migrations.Migration):
    initial = True

    dependencies: ClassVar[tuple[tuple[str, str], ...]] = (
        ("inventory", "0003_merge_0002_add_sku_0002_add_status"),
    )

    operations: ClassVar[tuple[Operation, ...]] = (
        migrations.CreateModel(
            name="CatalogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
            ],
        ),
    )
