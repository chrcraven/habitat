from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.activities"
    label = "activities"

    def ready(self):
        # Registers the post_save signal that seeds a default workflow
        # for every new Organization. Imported here (not at module import
        # time) to avoid a circular import between apps.accounts and
        # apps.activities.
        from . import signals  # noqa: F401
