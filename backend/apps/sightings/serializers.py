from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.species.serializers import SpeciesSerializer

from .models import Sighting, SightingPhoto


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
