from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Activity, ActivityPhoto, WorkflowState


class WorkflowStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowState
        fields = ["id", "name", "is_planned", "is_done", "order"]


class ActivitySerializer(GeoFeatureModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    # Species linking (through ActivitySpecies, with role/quantity/detail)
    # isn't wired up on this endpoint yet — Django M2M .set() doesn't work
    # against a custom `through` model, so writing this needs its own
    # nested-create handling. Read-only names for display in the
    # meantime; see /CLAUDE.md task log.
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
