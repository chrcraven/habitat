from rest_framework import serializers

from .models import Species


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = ["id", "common_name", "scientific_name", "notes", "created_at"]
