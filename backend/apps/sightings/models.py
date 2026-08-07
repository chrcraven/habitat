"""
Sightings: a wildlife (or other) observation, deliberately modeled
differently from Activity — point location instead of a drawn shape, and
no planned/done lifecycle. See /docs/data-model-notes.md ("Sighting
record").
"""

from django.contrib.gis.db import models as gis_models
from django.db import models

from apps.accounts.models import Organization, Property, User
from apps.species.models import Species


class Sighting(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="sightings"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sightings",
        help_text="Optional — a sighting's point may or may not fall "
        "within a drawn property boundary.",
    )
    species = models.ForeignKey(
        Species, on_delete=models.PROTECT, related_name="sightings"
    )
    location = gis_models.PointField(srid=4326)
    observed_at = models.DateTimeField(
        help_text="When the sighting occurred, which may differ from when "
        "it was logged."
    )
    notes = models.TextField(blank=True)

    is_public = models.BooleanField(
        default=True,
        help_text="Sightings are public by default; uncheck to make this "
        "one record private. NOTE: no auto-private default yet for "
        "sensitive/at-risk species — see /docs/open-questions.md "
        "('Sensitive sighting default behavior'). Set this manually for "
        "any sighting where public location data could cause harm.",
    )

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="sightings_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-observed_at"]

    def __str__(self):
        return f"{self.species} sighting @ {self.observed_at:%Y-%m-%d}"


class SightingPhoto(models.Model):
    """Same DB-storage decision as ActivityPhoto — see
    /docs/data-model-notes.md and /docs/tech-stack-options.md."""

    sighting = models.ForeignKey(
        Sighting, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.BinaryField()
    content_type = models.CharField(max_length=100)
    captured_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.sighting} ({self.uploaded_at:%Y-%m-%d})"


class SightingActivityLink(models.Model):
    """The direct many-to-many link between a Sighting and an Activity.
    Decided: created directly, not gated behind resolving a Task — see
    /docs/data-model-notes.md ("Do sightings and activities share a data
    model?")."""

    sighting = models.ForeignKey(Sighting, on_delete=models.CASCADE)
    activity = models.ForeignKey("activities.Activity", on_delete=models.CASCADE)
    linked_at = models.DateTimeField(auto_now_add=True)
    linked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["sighting", "activity"], name="unique_sighting_activity_link"
            )
        ]

    def __str__(self):
        return f"{self.sighting} ↔ {self.activity}"
