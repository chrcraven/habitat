from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """Org-scoped shape — submission (POST) and an admin's own-org review
    list (GET), see views.py#feedback_list_or_submit."""

    submitted_by_email = serializers.CharField(
        source="submitted_by.email", read_only=True, default=None
    )

    class Meta:
        model = Feedback
        fields = [
            "id",
            "message",
            "page_path",
            "status",
            "submitted_by_email",
            "created_at",
            "synced_at",
            "resolved_at",
        ]
        # page_path is set by the view from the submitted value after
        # validation (see views.py#feedback_list_or_submit), not written
        # straight through from the request body.
        read_only_fields = ["page_path", "status", "synced_at", "resolved_at"]


class FeedbackPullSerializer(serializers.ModelSerializer):
    """Cross-org shape for the external routine's pull (see views.py
    #feedback_pull) — includes the organization name since, unlike every
    other endpoint in the app, this one isn't scoped to a single caller's
    organization."""

    organization_name = serializers.CharField(source="organization.name", read_only=True)
    submitted_by_email = serializers.CharField(
        source="submitted_by.email", read_only=True, default=None
    )

    class Meta:
        model = Feedback
        fields = [
            "id",
            "organization_name",
            "submitted_by_email",
            "message",
            # The screen the submitter was on — the whole point of
            # capturing it is that it reaches the build queue, so it has
            # to be in the pull payload, not just the admin's own list.
            "page_path",
            "status",
            "created_at",
        ]
