"""
Accounts: users, organizations, properties, membership/roles.

See /docs/data-model-notes.md ("Accounts / ownership...") for the full
rationale. Key decision baked in here: there is exactly one account/org
model, not a separate "individual" vs "organization" type — a solo
homeowner's Organization just happens to have one Membership.
"""

import secrets
from datetime import timedelta

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils import timezone


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
    # Whole-property public/private, separate from and in addition to each
    # Activity/Sighting's own per-record is_public flag (see
    # /docs/data-model-notes.md). Added alongside the Phase 2 public site
    # (see /CLAUDE.md task log): an org managing a public property
    # (e.g. a land trust's preserve) and a private one (e.g. a
    # homeowner-manager's own yard) under the same account needs to be
    # able to keep the latter off the public site entirely, not just rely
    # on marking every individual record private. Default True to match
    # the existing public-by-default stance on activity/sighting records.
    is_public = models.BooleanField(default=True)
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
    # Default is the *minimal* role, not admin — signup explicitly grants
    # the account creator Role.ADMIN (see apps/accounts/views.py:signup);
    # any Membership created without an explicit role (e.g. a future
    # invite flow, Phase 3) starts a new contributor at read-only access
    # until an existing admin expands it. See /docs/open-questions.md
    # ("Exact role definitions") — capabilities are: viewer = read only,
    # editor = read/create/update, admin = also delete. Enforced in
    # apps/accounts/org_scoping.py's OrganizationRolePermission.
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
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


def _generate_invitation_token():
    """Opaque, unguessable token generator — despite the name (kept as-is
    so the existing Invitation migration's stored function reference stays
    valid), also used as PasswordResetToken.token's default below."""
    return secrets.token_urlsafe(32)


class Invitation(models.Model):
    """A pending, not-yet-accepted invite for someone to join an
    Organization — resolves the "real email-invite flow" gap in
    /docs/open-questions.md ("Auth and API"), which until now meant an
    admin had to set a brand-new member's initial password directly and
    share it out of band (see MembershipViewSet in views.py's old
    docstring / git history).

    Deliberately its own model rather than an unaccepted Membership: an
    Invitation has no `user` yet (the invitee may not have an account at
    all), carries the role/property scope the *acceptor* will get once
    they sign up through it, and expires — none of which make sense on
    Membership itself. Accepting one creates the User + Membership
    together (see apps/accounts/views.py#invitation_accept), same shape as
    signup's "create everything in one step" but joining an *existing*
    org instead of a new one.
    """

    EXPIRY = timedelta(days=7)

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Membership.Role.choices, default=Membership.Role.VIEWER)
    properties = models.ManyToManyField(
        Property, blank=True, related_name="scoped_invitations"
    )
    invited_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="sent_invitations"
    )
    # Opaque, unguessable — this is the only thing that authorizes
    # accepting the invite, so it has to be long and random rather than
    # e.g. the row's own id.
    token = models.CharField(max_length=64, unique=True, default=_generate_invitation_token)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return self.accepted_at is None and timezone.now() > self.created_at + self.EXPIRY

    def __str__(self):
        return f"{self.email} -> {self.organization} ({self.role})"


class PasswordResetToken(models.Model):
    """A one-time, short-lived token authorizing a single password reset —
    resolves the "forgot password" gap noted in /docs/open-questions.md
    ("Auth and API"): before this, a member who forgot their password had
    no self-service way back in at all (self-service *change* already
    existed — see User-facing `/account` page — but that requires already
    being logged in with the old password).

    Deliberately its own model rather than reusing Invitation: this has no
    organization/role/property scope, expires much sooner (an hour, not a
    week — a reset link sitting in an inbox is a bigger risk than an
    invite link), and is one-time-use (`used_at`) rather than
    accept-once-ever being the same thing as "has a value."
    """

    EXPIRY = timedelta(hours=1)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="password_resets"
    )
    token = models.CharField(max_length=64, unique=True, default=_generate_invitation_token)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return self.used_at is None and timezone.now() > self.created_at + self.EXPIRY

    def __str__(self):
        return f"reset for {self.user}"
