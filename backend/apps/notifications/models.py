"""
In-app notifications — the first (and, for now, only) implementation of
the pluggable channel dispatch in events.py. See
/docs/open-questions.md ("Task assignee notification", decided
2026-08-29): ship in-app now, but architect for pluggable channels so
email (once real SMTP exists — see "Real email delivery isn't
configured") or anything else can be added later without reworking this.

Deliberately generic (`verb`/`message`) rather than task-specific, even
though task assignment is the only event that creates one today — see
apps/tasks/views.py#TaskViewSet — so a future event type doesn't need a
schema change, just a new Verb choice and call site.
"""

from django.db import models

from apps.accounts.models import Organization, User


class Notification(models.Model):
    class Verb(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task assigned"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="notifications"
    )
    # Who sees this — a notification is inherently personal, unlike almost
    # everything else in the app, which is scoped to an active
    # organization rather than a specific user (see org_scoping.py).
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    verb = models.CharField(max_length=50, choices=Verb.choices)
    message = models.CharField(max_length=255)
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_verb_display()} -> {self.recipient} ({'read' if self.is_read else 'unread'})"
