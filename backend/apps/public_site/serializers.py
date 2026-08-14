"""
Photo serializers for the public site, distinct from
apps/activities/serializers.py's ActivityPhotoSerializer (and sightings'
equivalent) only in which `url` they build — the authenticated ones point
at a session-cookie-gated image endpoint, which an anonymous visitor can't
use. These point at the AllowAny public image endpoints in this app's
views.py instead. Everything else (Property/Activity/Sighting) is
serialized with the existing app serializers unchanged — same fields are
fine to show publicly since they're already filtered to is_public=True
records before they ever reach a serializer here (see views.py).
"""

from rest_framework import serializers
from rest_framework.reverse import reverse

from apps.activities.models import ActivityPhoto
from apps.sightings.models import SightingPhoto


class PublicActivityPhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ActivityPhoto
        fields = ["id", "url", "content_type", "captured_at", "uploaded_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        path = reverse(
            "public-activity-photo-image",
            kwargs={"activity_id": obj.activity_id, "photo_id": obj.id},
        )
        return request.build_absolute_uri(path) if request else path


class PublicSightingPhotoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = SightingPhoto
        fields = ["id", "url", "content_type", "captured_at", "uploaded_at"]

    def get_url(self, obj):
        request = self.context.get("request")
        path = reverse(
            "public-sighting-photo-image",
            kwargs={"sighting_id": obj.sighting_id, "photo_id": obj.id},
        )
        return request.build_absolute_uri(path) if request else path
