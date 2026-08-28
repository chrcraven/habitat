from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .invitations import accept_url
from .models import Invitation, Membership, Organization, Property, User


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


class MembershipDetailSerializer(serializers.ModelSerializer):
    """Used by the org admin portal's member list/management endpoints
    (see views.py's MembershipViewSet) — distinct from the plain
    MembershipSerializer above (used only in the auth session payload,
    where the org doesn't need its member's full property scope)."""

    user = UserSerializer(read_only=True)
    properties = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    property_names = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ["id", "user", "role", "properties", "property_names", "created_at"]

    def get_property_names(self, obj):
        return [p.name for p in obj.properties.all()]


class InvitationSerializer(serializers.ModelSerializer):
    """A pending invite, as shown in the org admin portal's "Pending
    invitations" list (see views.py's InvitationViewSet) and returned when
    one is first created. `accept_url` is always included — see
    apps/accounts/invitations.py's module docstring for why it isn't just
    an email-only flow."""

    property_names = serializers.SerializerMethodField()
    invited_by_email = serializers.SerializerMethodField()
    accept_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "role",
            "property_names",
            "invited_by_email",
            "accept_url",
            "created_at",
            "is_expired",
        ]

    def get_property_names(self, obj):
        return [p.name for p in obj.properties.all()]

    def get_invited_by_email(self, obj):
        return obj.invited_by.email if obj.invited_by else None

    def get_accept_url(self, obj):
        return accept_url(obj.token)


class PropertySerializer(GeoFeatureModelSerializer):
    """`boundary` is nullable on the model (a property can be named before
    its shape is drawn) — GeoFeatureModelSerializer serializes that as a
    Feature with `geometry: null`, and accepts the field being omitted or
    null on write too."""

    class Meta:
        model = Property
        geo_field = "boundary"
        fields = [
            "id",
            "name",
            "boundary",
            "is_public",
            "sightings_public_by_default",
            "created_at",
            "updated_at",
        ]
