from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"

    def ready(self):
        # Importing the module is what registers its @register() check.
        # This package owns both of Habitat's send_mail call sites
        # (password_reset.py, invitations.py), which is why the mail
        # transport check lives here rather than in config/.
        from . import checks  # noqa: F401
