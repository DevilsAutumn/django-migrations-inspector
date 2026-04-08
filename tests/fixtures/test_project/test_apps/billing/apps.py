"""App configuration for the billing fixture app."""

from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Register the billing fixture app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tests.fixtures.test_project.test_apps.billing"
    label = "billing"
