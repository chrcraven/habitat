from rest_framework import serializers

from apps.accounts.models import Membership
from apps.accounts.org_scoping import get_active_membership

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """A simple, optional, user-to-user assignable to-do (see
    /docs/data-model-notes.md, "Task record") — deliberately kept plain:
    no notifications, no due dates, no rules-engine auto-creation (Phase
    4). `assigned_to`/`origin_sighting`/`origin_activity` are all
    optional and, when set, are validated against the caller's own
    organization in the `validate_*` methods below — nothing here
    prevents assigning a task to, or originating it from, a record
    outside the org otherwise, since none of those FKs point at
    Organization directly."""

    assigned_to_email = serializers.CharField(
        source="assigned_to.email", read_only=True, default=None
    )
    created_by_email = serializers.CharField(
        source="created_by.email", read_only=True, default=None
    )
    origin_sighting_species = serializers.CharField(
        source="origin_sighting.species.common_name", read_only=True, default=None
    )
    origin_activity_type = serializers.CharField(
        source="origin_activity.activity_type", read_only=True, default=None
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "origin_sighting",
            "origin_sighting_species",
            "origin_activity",
            "origin_activity_type",
            "assigned_to",
            "assigned_to_email",
            "status",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def _active_organization(self):
        request = self.context.get("request")
        membership = get_active_membership(request.user) if request else None
        return membership.organization if membership else None

    def validate_assigned_to(self, value):
        if value is None:
            return value
        organization = self._active_organization()
        if not Membership.objects.filter(user=value, organization=organization).exists():
            raise serializers.ValidationError(
                "That person isn't a member of this organization."
            )
        return value

    def validate_origin_sighting(self, value):
        if value is not None and value.organization_id != self._active_organization().id:
            raise serializers.ValidationError("That sighting isn't part of this organization.")
        return value

    def validate_origin_activity(self, value):
        if value is not None and value.organization_id != self._active_organization().id:
            raise serializers.ValidationError("That activity isn't part of this organization.")
        return value
