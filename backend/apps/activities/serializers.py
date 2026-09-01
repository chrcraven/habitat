from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.accounts.org_scoping import get_active_membership, property_accessible

from .models import Activity, ActivityPhoto, ActivitySpecies, WorkflowState


class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = ["id", "name", "is_planned", "is_done", "order"]


class ActivitySpeciesSerializer(serializers.ModelSerializer):
    """The Activity↔Species through-model (role/quantity/detail per
    species on an activity — e.g. a planting of three species, or a
    treatment targeting one invasive). Django M2M `.set()` doesn't work
    against a custom `through` model, so this is its own
    create/update/delete surface (apps/activities/views.py's
    activity_species_list/detail) rather than a nested write inside
    ActivitySerializer — same shape as SightingActivityLinkSerializer's
    relationship to the sighting/activity endpoints."""

    species_name = serializers.CharField(source="species.common_name", read_only=True)

    class Meta:
        model = ActivitySpecies
        fields = ["id", "activity", "species", "species_name", "role", "quantity", "detail"]
        read_only_fields = ["activity"]


class ActivitySerializer(GeoFeatureModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    # Read-only convenience mirroring the activity's current WorkflowState —
    # lets the map (and anything else) style/group by done-vs-not without
    # its own copy of the org's workflow. Deliberately just `is_done`, not
    # also `is_planned`: a custom workflow's non-planned, non-done states
    # (e.g. "In Progress") are still meaningfully "not done yet" for the
    # planned-vs-completed map distinction Phase 2 calls for, and treating
    # them as a third bucket would require an opinion on whether every
    # workflow reserves a "planned" state, which is still an open question
    # (see docs/open-questions.md).
    is_done = serializers.BooleanField(source="status.is_done", read_only=True)
    # Read-only convenience for display (e.g. an activity list row) —
    # writing species onto an activity goes through the dedicated
    # /activities/<id>/species/ endpoints above, not this field.
    species_names = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        geo_field = "geometry"
        fields = [
            "id",
            "property",
            "activity_type",
            "status",
            "status_name",
            "is_done",
            "geometry",
            "date_planned",
            "date_done",
            "notes",
            "is_public",
            "species_names",
            "created_at",
            "updated_at",
        ]

    def get_species_names(self, obj):
        return [s.common_name for s in obj.species.all()]

    def validate_property(self, value):
        # Was previously unvalidated — any authenticated editor could set
        # this to *any* Property row, including one belonging to another
        # organization entirely (the auto-generated PrimaryKeyRelatedField
        # queries Property.objects.all(), not scoped by org). Since the
        # public site derives a property's activities straight off this FK
        # (apps/public_site/views.py#property_activities), that let one
        # org's editor plant a fabricated activity on a *different* org's
        # public property page. Fixed the same way TaskSerializer/
        # PageSerializer already validate their own FKs: require the
        # caller's active membership to actually have access to it (same
        # org, and — if property-scoped — one of its own properties). See
        # /docs/open-questions.md, "Property-scoped role enforcement".
        request = self.context.get("request")
        membership = get_active_membership(request.user) if request else None
        if not property_accessible(membership, value):
            raise serializers.ValidationError("That property isn't accessible to you.")
        return value


class ActivityPhotoSerializer(serializers.ModelSerializer):
    """The binary `image` field itself is never serialized to JSON — `url`
    points at the dedicated byte-serving view (see views.py) so it can be
    used directly as an <img src>."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = ActivityPhoto
        fields = ["id", "url", "content_type", "captured_at", "uploaded_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        path = reverse(
            "activity-photo-image", kwargs={"activity_id": obj.activity_id, "photo_id": obj.id}
        )
        return request.build_absolute_uri(path) if request else path
