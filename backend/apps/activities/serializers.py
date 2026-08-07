from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Activity, WorkflowState


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
