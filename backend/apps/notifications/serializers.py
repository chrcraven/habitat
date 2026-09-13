from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializes a notification *including which organization it belongs
    to*, which matters more here than anywhere else in the app.

    Every other read endpoint is scoped to the caller's active
    organization (see apps/accounts/org_scoping.py), so the answer to
    "which org is this about?" is always "the one you're in" and never
    needs saying. `notification_list` is the single deliberate exception —
    it filters on `recipient` only, because a notification is personal and
    should reach you whichever org happens to be active. That intent is
    right, and it is exactly why the attribution has to travel: a
    notification is the one payload in this app whose organization is not
    implied by the request that fetched it.

    Without `organization`/`organization_name` the client was not merely
    failing to *display* the attribution — it was never sent it, so no
    amount of frontend work could have shown which org a message came
    from (D28, /docs/open-questions.md). Keep both: the id is what the
    client compares against the active membership to decide whether a
    notification is from elsewhere, and the name is what it renders.
    Sending only the name would force the client to string-match.
    """

    task_title = serializers.CharField(source="task.title", read_only=True, default=None)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "verb",
            "message",
            "organization",
            "organization_name",
            "task",
            "task_title",
            "is_read",
            "created_at",
        ]
