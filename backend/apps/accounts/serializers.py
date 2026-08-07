from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import Membership, Organization, Property, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "role"]


class PropertySerializer(GeoFeatureModelSerializer):
    """`boundary` is nullable on the model (a property can be named before
    its shape is drawn) — GeoFeatureModelSerializer serializes that as a
    Feature with `geometry: null`, and accepts the field being omitted or
    null on write too."""

    class Meta:
        model = Property
        geo_field = "boundary"
        fields = ["id", "name", "boundary", "created_at", "updated_at"]
