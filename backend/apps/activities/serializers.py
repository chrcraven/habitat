from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.accounts.org_scoping import get_active_membership, property_accessible

from .models import Activity, ActivityPhoto, ActivitySpecies, ActivityType, WorkflowState


class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = ["id", "name", "is_planned", "is_done", "order"]


class ActivityTypeSerializer(serializers.ModelSerializer):
    """An org's own activity types (see models.py#ActivityType). `name` is
    both the stored value and the display label — there's no slug, which
    is what stops the lowercase-value display problem from coming back."""

    class Meta:
        model = ActivityType
        fields = ["id", "name", "order"]

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("A name is required.")
        # UniqueConstraint is on (organization, name), and organization is
        # supplied by the viewset rather than the request body, so DRF's
        # auto-generated unique-together validator can't see it — check it
        # here against the caller's own org instead.
        organization = self.context.get("organization")
        clashes = ActivityType.objects.filter(organization=organization, name__iexact=name)
        if self.instance is not None:
            clashes = clashes.exclude(pk=self.instance.pk)
        if clashes.exists():
            raise serializers.ValidationError("You already have an activity type with that name.")
        return name


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
    # The human-readable type, mirroring `status_name` above. Added
    # 2026-09-02 because the client had nothing else to render: the old
    # fixed enum's labels only ever existed server-side, so every list row
    # showed the raw lowercase value. Keeping the label on the server (a
    # serializer field) rather than a label map in the frontend is also
    # what stops the app and the public site drifting apart — both read
    # this same serializer.
    activity_type_name = serializers.CharField(source="activity_type.name", read_only=True)
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
            "activity_type_name",
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

    def _ensure_own_org(self, value, label):
        """Both of an Activity's org-defined FKs (its type and its status)
        are auto-generated PrimaryKeyRelatedFields, which query the whole
        table — so without this, an editor could point either at another
        organization's row just by knowing its id. Same fix, and the same
        reason, as validate_property above."""
        request = self.context.get("request")
        membership = get_active_membership(request.user) if request else None
        if membership is None or value.organization_id != membership.organization_id:
            raise serializers.ValidationError(f"That {label} isn't one of your organization's.")
        return value

    def validate_activity_type(self, value):
        return self._ensure_own_org(value, "activity type")

    def validate_status(self, value):
        return self._ensure_own_org(value, "workflow state")


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
