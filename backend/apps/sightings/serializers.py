from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.species.serializers import SpeciesSerializer

from .models import Sighting, SightingActivityLink, SightingPhoto


class SightingSerializer(GeoFeatureModelSerializer):
    species_detail = SpeciesSerializer(source="species", read_only=True)

    class Meta:
        model = Sighting
        geo_field = "location"
        fields = [
            "id",
            "property",
            "species",
            "species_detail",
            "location",
            "observed_at",
            "notes",
            "is_public",
            "created_at",
            "updated_at",
        ]


class SightingActivityLinkSerializer(serializers.ModelSerializer):
    """The direct Sighting↔Activity link (see models.py) — surfaced from
    both sides (apps/sightings/views.py's sighting_links and
    apps/activities/views.py's activity_links use this same serializer),
    with just enough denormalized display fields (species/activity type/
    property name) that a link list doesn't need a second round-trip to
    show something meaningful."""

    activity_type = serializers.CharField(source="activity.activity_type", read_only=True)
    activity_property_name = serializers.CharField(
        source="activity.property.name", read_only=True
    )
    sighting_species = serializers.CharField(
        source="sighting.species.common_name", read_only=True
    )
    sighting_observed_at = serializers.DateTimeField(
        source="sighting.observed_at", read_only=True
    )

    class Meta:
        model = SightingActivityLink
        fields = [
            "id",
            "sighting",
            "activity",
            "activity_type",
            "activity_property_name",
            "sighting_species",
            "sighting_observed_at",
            "linked_at",
        ]
        read_only_fields = ["linked_at"]


class SightingPhotoSerializer(serializers.ModelSerializer):
    """Same shape as ActivityPhotoSerializer — see that class's docstring."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = SightingPhoto
        fields = ["id", "url", "content_type", "captured_at", "uploaded_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        path = reverse(
            "sighting-photo-image", kwargs={"sighting_id": obj.sighting_id, "photo_id": obj.id}
        )
        return request.build_absolute_uri(path) if request else path
