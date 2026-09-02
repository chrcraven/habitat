from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .invitations import accept_url
from .models import Invitation, Membership, Organization, Property, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]


class OrganizationSerializer(serializers.ModelSerializer):
    # The header banner image itself is never serialized as raw bytes over
    # JSON — this just tells the frontend whether one exists, so it knows
    # whether to render an <img> at all (pointed at the dedicated
    # theme-image endpoint — see views.py#organization_theme_image /
    # apps/public_site/views.py's public equivalent — rather than at
    # anything on this response).
    has_theme_header_image = serializers.SerializerMethodField()
    # Both custom-HTML gates resolved into one boolean the frontend can act
    # on (see apps/pages/custom_html.py): whether this org may author
    # custom-HTML pages at all. Read-only on purpose — the per-tenant half
    # is a kill-switch operated from Django admin, and an org that had its
    # custom content switched off must not be able to switch it back on
    # through its own admin console.
    custom_html_enabled = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "landing_page",
            "custom_html_enabled",
            "theme_primary_color",
            "theme_background_color",
            "theme_accent_color",
            "theme_font",
            "has_theme_header_image",
            "created_at",
        ]
        # slug is auto-generated from name on create (Organization.save);
        # an admin can override it via the org admin portal PATCH. Blank on
        # write means "regenerate from the name" (save() re-slugifies an
        # empty slug), which is the reset-to-default path.
        extra_kwargs = {"slug": {"required": False}}

    def get_has_theme_header_image(self, obj):
        return bool(obj.theme_header_image_content_type)

    def get_custom_html_enabled(self, obj):
        from apps.pages.custom_html import organization_allows_custom_html

        return organization_allows_custom_html(obj)

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

    def validate_landing_page(self, value):
        """`landing_page` picks which page shows at the public URL root —
        see Organization.landing_page's docstring. Must be one of this
        org's own **org-level** pages (property IS NULL); null means the
        built-in Explore view stays the landing page."""
        if value is None:
            return value
        organization = self.instance
        if organization is None or value.organization_id != organization.id or value.property_id is not None:
            raise serializers.ValidationError(
                "The landing page must be one of this organization's own pages."
            )
        return value


class MembershipSerializer(serializers.ModelSerializer):
    """Used in the auth session payload (`/api/auth/me` and friends) — the
    caller's own membership. Includes `properties` (ids) so the frontend
    can tell whether *this* member is property-scoped and hide actions
    that scoping now actually blocks (e.g. "+ New property" — see
    PropertyViewSet.perform_create) rather than showing a control that
    always 403s. Just ids, not `property_names` — a scoped member already
    sees those properties' names in their own properties list; this is
    only ever used to answer "am I scoped at all," not to render a list."""

    organization = OrganizationSerializer(read_only=True)
    properties = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "organization", "role", "properties"]


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

    # See OrganizationSerializer.has_theme_header_image's docstring —
    # same reasoning, per-property here.
    has_theme_header_image = serializers.SerializerMethodField()

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
            "landing_page",
            "theme_primary_color",
            "theme_background_color",
            "theme_accent_color",
            "theme_font",
            "has_theme_header_image",
            "created_at",
            "updated_at",
        ]
        # slug auto-generates from name on create (Property.save); admin can
        # override on the edit form. Blank means "regenerate from the name".
        extra_kwargs = {"slug": {"required": False}}

    def get_has_theme_header_image(self, obj):
        return bool(obj.theme_header_image_content_type)

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

    def validate_landing_page(self, value):
        """Mirror of OrganizationSerializer.validate_landing_page, but for
        this property's own pages (Page.property == this property) rather
        than an org-level page."""
        if value is None:
            return value
        property_ = self.instance
        if property_ is None or value.property_id != property_.id:
            raise serializers.ValidationError(
                "The landing page must be one of this property's own pages."
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
