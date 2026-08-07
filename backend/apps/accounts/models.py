"""
Accounts: users, organizations, properties, membership/roles.

See /docs/data-model-notes.md ("Accounts / ownership...") for the full
rationale. Key decision baked in here: there is exactly one account/org
model, not a separate "individual" vs "organization" type — a solo
homeowner's Organization just happens to have one Membership.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.gis.db import models as gis_models
from django.db import models


class UserManager(BaseUserManager):
    """Email is the username field — no separate username, per the decided
    email/password auth model (see /docs/open-questions.md, "Recently
    resolved")."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """A human contributor. Belongs to one or more Organizations via
    Membership. Third-party API consumers (Phase 4) will authenticate with
    API keys instead of a User — not modeled yet."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Organization(models.Model):
    """The top-level owner of data. Every account is structurally an
    organization, whether it currently has one contributor (the common
    Phase 1 case) or many. See /docs/data-model-notes.md."""

    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Property(models.Model):
    """A piece of land with a user-drawn boundary, owned by an
    Organization. Boundary is deliberately not validated against cadastral
    parcel data (decided — see /docs/data-model-notes.md). `boundary` is
    nullable so a property can be named before its boundary is drawn."""

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="properties"
    )
    name = models.CharField(max_length=255)
    boundary = gis_models.PolygonField(srid=4326, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"

    def __str__(self):
        return f"{self.name} ({self.organization})"


class Membership(models.Model):
    """A User's role within an Organization, optionally scoped to specific
    Properties.

    Simplification for Phase 1: one Membership per (user, organization)
    pair, with a single role that is either account-wide (no properties
    selected) or scoped to the selected properties. The exact role set is
    still open — see /docs/open-questions.md ("Exact role definitions").
    If a person ever needs *different* roles on different property scopes
    within the same org, this model will need to allow multiple Memberships
    per (user, organization) instead of enforcing uniqueness — not needed
    for the author's own dogfooding use case yet, so deferred rather than
    over-built now.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    properties = models.ManyToManyField(
        Property,
        blank=True,
        related_name="scoped_memberships",
        help_text="Leave empty for an account-wide role; select specific "
        "properties to scope this role to just those.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization"], name="unique_user_per_organization"
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.role} @ {self.organization}"
