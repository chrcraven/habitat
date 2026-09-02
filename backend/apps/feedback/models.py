"""
In-app feedback on Habitat itself, from Habitat's own logged-in users —
deliberately not the Phase 5 "public input" concept (visitor-submitted
land-management data on the public site, still open in
/docs/open-questions.md). This is bug reports / UX friction / feature
ideas from an org member, meant to reach the project's own build workflow
without the owner having to query the database by hand — see
/docs/open-questions.md ("App feedback / build workflow") for the full
decided shape.

Status is a three-stage lifecycle, not just a submitted/handled boolean,
specifically so the *pull* (has this row already been fetched into
build-questions.md) and the *underlying resolution* (has the actual
request been addressed) don't get conflated — a row can be `synced`
(already recorded, so the next pull correctly skips it) while the
feature/bug it describes is still genuinely open:

  new -> synced (pulled by the external routine, see apps/feedback/views.py
         #feedback_pull/#feedback_mark_synced) -> resolved (an org admin
         marks it once the request is actually addressed, see
         #feedback_resolve — independent of when it was synced).
"""

from django.db import models

from apps.accounts.models import Organization, User


class Feedback(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        SYNCED = "synced", "Synced"
        RESOLVED = "resolved", "Resolved"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="feedback_items"
    )
    submitted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="feedback_submitted"
    )
    message = models.TextField()
    # Which screen the submitter was on (owner request, 2026-09-02: "would
    # likely give context to the build to know where to start"). A *path*,
    # not a full URL — the host is implied by which instance was pulled,
    # and the path is what identifies the screen. Optional on purpose: an
    # older client, or a submission that arrives without one, still
    # succeeds rather than 400ing on a context field. Validated in
    # views.py#feedback_list_or_submit rather than here, so a non-path
    # value is dropped instead of rejecting the feedback itself.
    page_path = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"feedback from {self.submitted_by} ({self.status})"
