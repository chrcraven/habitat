from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.species.serializers import SpeciesSerializer

from .models import Sighting


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
