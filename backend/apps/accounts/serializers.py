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
        fields = ["id", "name", "slug", "created_at"]
        # slug is auto-generated from name on create (Organization.save);
        # an admin can override it via the org admin portal PATCH. Blank on
        # write means "regenerate from the name" (save() re-slugifies an
        # empty slug), which is the reset-to-default path.
        extra_kwargs = {"slug": {"required": False}}

    def validate_slug(self, value):
        from .slugs import RESERVED_ORG_SLUGS

        if not value:
            # Empty -> let Organization.save() regenerate from the name.
            return value
        if value in RESERVED_ORG_SLUGS:
            raise serializers.ValidationError(
                "That URL name is reserved — please choose another."
            )
        qs = Organization.objects.filter(slug=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("That URL name is already taken.")
        return value


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
            "slug",
            "boundary",
            "is_public",
            "sightings_public_by_default",
            "created_at",
            "updated_at",
        ]
        # slug auto-generates from name on create (Property.save); admin can
        # override on the edit form. Blank means "regenerate from the name".
        extra_kwargs = {"slug": {"required": False}}

    def validate_slug(self, value):
        if not value:
            # Empty -> Property.save() regenerates from the name.
            return value
        # Property slugs only need to be unique within their own org.
        organization = None
        if self.instance is not None:
            organization = self.instance.organization
        else:
            from .org_scoping import get_active_membership

            request = self.context.get("request")
            membership = get_active_membership(request.user) if request else None
            organization = membership.organization if membership else None
        if organization is not None:
            qs = Property.objects.filter(organization=organization, slug=value)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "Another property in your organization already uses that URL name."
                )
        return value


class DeletedPropertySerializer(serializers.ModelSerializer):
    """The org admin portal's "Recently deleted" list (see views.py's
    PropertyViewSet.deleted/restore) — a soft-deleted property, not yet
    purged. Deliberately its own (much smaller) serializer rather than
    reusing PropertySerializer: this list doesn't need the boundary
    geometry or public-visibility fields, just enough to identify the
    property and show the restore window."""

    purge_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Property
        fields = ["id", "name", "deleted_at", "purge_at"]
