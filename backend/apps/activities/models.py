"""
Activities: the individual land manager's core unit of work (a seeding,
planting, treatment, or other intervention). See
/docs/data-model-notes.md ("Activity record").
"""

from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.accounts.models import Organization, Property, User
from apps.species.models import Species


class WorkflowState(models.Model):
    """One state in an Organization's own activity-status workflow.

    Decided: status states beyond the planned/done pair are org-defined,
    not a fixed global enum (see /docs/data-model-notes.md and
    /docs/open-questions.md). `is_planned`/`is_done` mark which of an
    org's custom states count as the reserved planned/done-equivalent
    states the public view (Phase 2+) depends on — still open whether every
    workflow is *required* to designate one of each; for now the app just
    supports flagging them per /docs/open-questions.md ("Are planned/done-
    equivalent states reserved?").

    A default workflow (Planned → In Progress → Done) is seeded for every
    new Organization via a post_save signal (see signals.py) so a solo
    user isn't forced to configure a workflow before logging their first
    activity — see the task log in /CLAUDE.md for this assumption.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="workflow_states"
    )
    name = models.CharField(max_length=100)
    is_planned = models.BooleanField(default=False)
    is_done = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["organization_id", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="unique_state_name_per_organization"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.organization})"


class ActivityType(models.Model):
    """One kind of work an Organization does — a seeding, a planting, a
    treatment, whatever that org actually calls it.

    Decided 2026-09-02 (owner, answering real user feedback: *"I'd like
    the activities enum to be editable"*): this was a fixed `TextChoices`
    enum on Activity until then, and the model's own docstring had carried
    the "should this become org-defined the way status states already
    are?" question since the first backend session. It should, and this is
    that change — deliberately shaped as a near-copy of `WorkflowState`
    above rather than a second, different pattern for the same idea:
    per-org rows, a unique name within the org, an explicit display
    `order`, and a default set seeded for every new Organization by a
    post_save signal (see signals.py).

    `name` is both the stored value and the human label — that's the point
    of the change. The old enum kept a lowercase slug alongside a proper
    label ("seeding" / "Seeding") and the API only ever exposed the slug,
    which is exactly the second half of the same feedback (*"what is being
    displayed to the user is all lowercase"*). There is no slug here to
    leak: an org names its own types, the seed writes proper Title Case,
    and what's stored is what's shown.

    Consequence worth knowing: activity types are no longer comparable
    across organizations. That's inherent to org-defined reference data
    (`WorkflowState` and `Species` already have it) and matters mainly for
    any future cross-org reporting or Phase 4 API grouping — noted in
    /docs/data-model-notes.md rather than worked around here.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="activity_types"
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["organization_id", "order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"], name="unique_activity_type_per_organization"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.organization})"


class Activity(models.Model):
    """A seeding, planting, treatment, or other intervention. Geometry
    (not just a point) is the key structural difference from Sighting.

    `activity_type` became an org-defined FK (see ActivityType above) on
    2026-09-02, replacing the fixed enum this model carried through
    Phase 1.
    """

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="activities"
    )
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="activities"
    )
    # PROTECT, matching `status` below: a type that's in use can't be
    # deleted out from under its activities. The API turns the resulting
    # ProtectedError into a plain 400 with an explanation rather than a
    # 500 — see views.py#ActivityTypeViewSet.destroy.
    activity_type = models.ForeignKey(
        ActivityType, on_delete=models.PROTECT, related_name="activities"
    )
    status = models.ForeignKey(
        WorkflowState, on_delete=models.PROTECT, related_name="activities"
    )
    geometry = gis_models.PolygonField(srid=4326)

    date_planned = models.DateField(null=True, blank=True)
    date_done = models.DateField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    notes = models.TextField(blank=True)

    is_public = models.BooleanField(
        default=True,
        help_text="Activities are public by default; uncheck to make this "
        "one record private, overriding the account default.",
    )

    species = models.ManyToManyField(
        Species, through="ActivitySpecies", related_name="activities", blank=True
    )
    sightings = models.ManyToManyField(
        "sightings.Sighting",
        through="sightings.SightingActivityLink",
        related_name="linked_activities",
        blank=True,
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="activities_created"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "activities"
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.activity_type} @ {self.property} ({self.status})"


class ActivitySpecies(models.Model):
    """Through model linking an Activity to one or more Species — e.g. a
    planting of three species, or a treatment targeting one invasive
    species."""

    class SpeciesRole(models.TextChoices):
        PLANTED = "planted", "Planted"
        TREATED_TARGET = "treated_target", "Treated / targeted"
        OTHER = "other", "Other"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    species = models.ForeignKey(Species, on_delete=models.PROTECT)
    role = models.CharField(max_length=20, choices=SpeciesRole.choices, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    detail = models.CharField(
        max_length=255,
        blank=True,
        help_text="Free-text fallback/detail alongside the structured pick "
        "(e.g. method/product used for a treatment).",
    )

    class Meta:
        verbose_name_plural = "activity species"

    def __str__(self):
        return f"{self.species} on {self.activity}"


class ActivityPhoto(models.Model):
    """A photo attached to an Activity. Stored in the database (decided —
    see /docs/data-model-notes.md and /docs/tech-stack-options.md), not
    external object storage."""

    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.BinaryField()
    content_type = models.CharField(max_length=100)
    captured_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.activity} ({self.uploaded_at:%Y-%m-%d})"
