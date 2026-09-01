from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from apps.accounts.org_scoping import get_active_membership, property_accessible, scoped_property_ids
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

    def _membership(self):
        request = self.context.get("request")
        return get_active_membership(request.user) if request else None

    def validate_property(self, value):
        # Was previously unvalidated — same cross-org gap as
        # ActivitySerializer.validate_property (see that method's
        # docstring): any editor could set this to another organization's
        # property, and the public site's property_sightings view derives
        # a property's sightings straight off this FK. `property` is
        # optional on Sighting (a sighting may not fall within any drawn
        # boundary), so unlike Activity's version, None is left alone here
        # — see validate() below for the property-scoped-membership case,
        # where None isn't allowed either.
        if value is None:
            return value
        if not property_accessible(self._membership(), value):
            raise serializers.ValidationError("That property isn't accessible to you.")
        return value

    def validate_species(self, value):
        # Same class of gap as `property` above — Species is also
        # per-organization (the account-defined list, see
        # /docs/data-model-notes.md), and species_detail is serialized
        # straight into the public site's sighting payload.
        membership = self._membership()
        if membership is None or value.organization_id != membership.organization_id:
            raise serializers.ValidationError("That species isn't part of this organization.")
        return value

    def validate(self, attrs):
        # A property-scoped membership (see /docs/open-questions.md,
        # "Property-scoped role enforcement") can't create a sighting with
        # no property at all — such a sighting would be invisible to them
        # (and every other scoped member) afterward, per
        # SightingViewSet.get_queryset, since there'd be nothing to scope
        # it to. Only applies on create (self.instance is None); an
        # existing property-less sighting can still be edited without
        # forcing a property onto it retroactively.
        if self.instance is None:
            membership = self._membership()
            if scoped_property_ids(membership) is not None and attrs.get("property") is None:
                raise serializers.ValidationError(
                    {"property": "Your role is scoped to specific properties — choose one."}
                )
        return attrs


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
