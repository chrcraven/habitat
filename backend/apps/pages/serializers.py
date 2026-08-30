from rest_framework import serializers

from apps.accounts.models import Property

from .models import RESERVED_PAGE_SLUGS, Page


class PageSerializer(serializers.ModelSerializer):
    """The authoring/management shape — includes the raw `body` markdown
    source (for editing) rather than rendered HTML; the public site never
    uses this serializer, see apps/public_site/serializers.py's
    PublicPageSerializer for the sanitized-HTML shape it gets instead."""

    class Meta:
        model = Page
        fields = [
            "id",
            "property",
            "title",
            "slug",
            "body",
            "is_public",
            "position",
            "created_at",
            "updated_at",
        ]
        # slug auto-generates from title on create (Page.save); blank on
        # write means "regenerate from the title", same convention as
        # Organization/Property.
        extra_kwargs = {
            "slug": {"required": False},
            # Nullable/blank on the model (unset = an org-level page), but
            # DRF's auto-generated PrimaryKeyRelatedField doesn't infer
            # required=False from that the way it does for plain fields —
            # spell it out so omitting `property` means "org-level", not a
            # validation error.
            "property": {"required": False},
        }

    def get_unique_together_validators(self):
        """Meta.constraints has two *conditional* UniqueConstraints
        (organization+slug when property is null, property+slug when it
        isn't). DRF's auto-generated UniqueTogetherValidator can't express
        the "only applies when property is null" condition, and worse,
        it force-requires every field in the constraint to be present on
        every write (`enforce_required_fields`) — which would make
        `property` mandatory even for an org-level page, where omitting it
        is the whole point. `validate_slug` below already enforces
        uniqueness correctly for both scopes, so skip DRF's automatic
        validator entirely rather than fight it.
        """
        return []

    def validate_property(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        organization = self.context.get("organization")
        if organization is None and request is not None:
            from apps.accounts.org_scoping import get_active_membership

            membership = get_active_membership(request.user)
            organization = membership.organization if membership else None
        if organization is not None and value.organization_id != organization.id:
            raise serializers.ValidationError("That property isn't in your organization.")
        return value

    def validate_slug(self, value):
        if not value:
            # Empty -> Page.save() regenerates from the title.
            return value
        if value in RESERVED_PAGE_SLUGS:
            raise serializers.ValidationError(
                "\"explore\" is reserved for the built-in page — please choose another URL name."
            )
        # Scope (org-level vs. this property) is only fully known once
        # `property` itself has been validated — DRF validates fields in
        # declaration order, and `property` is declared before `slug` in
        # Meta.fields above, so `self.initial_data`/already-validated
        # attrs give us what we need here.
        property_id = self.initial_data.get("property", None)
        if self.instance is not None and "property" not in self.initial_data:
            property_id = self.instance.property_id
        qs = Page.objects.filter(slug=value)
        if property_id:
            qs = qs.filter(property_id=property_id)
        else:
            organization = self.context.get("organization")
            if organization is None:
                request = self.context.get("request")
                if request is not None:
                    from apps.accounts.org_scoping import get_active_membership

                    membership = get_active_membership(request.user)
                    organization = membership.organization if membership else None
            qs = qs.filter(organization=organization, property__isnull=True)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "Another page in this scope already uses that URL name."
            )
        return value


class PageOptionSerializer(serializers.ModelSerializer):
    """Minimal shape for a landing-page picker (id/title/slug only) — see
    OrganizationSerializer.pages / PropertySerializer.pages in
    apps/accounts/serializers.py."""

    class Meta:
        model = Page
        fields = ["id", "title", "slug"]
