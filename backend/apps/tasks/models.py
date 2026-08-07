"""
Tasks: a simple, optional, user-to-user assignable to-do — not a required
step for anything else in the model (in particular, not required for the
Sighting-Activity link). See /docs/data-model-notes.md ("Task record").

Kept intentionally simple for Phase 1: no notifications, no due dates, no
rules-engine auto-creation (that's Phase 4 — see /docs/roadmap.md).
"""

from django.db import models

from apps.accounts.models import Organization, User


class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ASSIGNED = "assigned", "Assigned"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # A task can reference a sighting or an activity, or neither (a
    # general to-do) — deliberately not the same thing as the direct
    # Sighting<->Activity link, see module docstring.
    origin_sighting = models.ForeignKey(
        "sightings.Sighting",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    origin_activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_assigned",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="tasks_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
