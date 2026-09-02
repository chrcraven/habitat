from rest_framework import serializers

from apps.accounts.models import Property

from .custom_html import max_html_bytes, organization_allows_custom_html
from .models import RESERVED_PAGE_SLUGS, ContentFormat, Page


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
            "content_format",
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

    def _organization(self):
        organization = self.context.get("organization")
        if organization is not None:
            return organization
        request = self.context.get("request")
        if request is None:
            return None
        from apps.accounts.org_scoping import get_active_membership

        membership = get_active_membership(request.user)
        return membership.organization if membership else None

    def validate(self, attrs):
        """The custom-HTML gates and size cap. Cross-field, so it can't be a
        `validate_content_format` — a PATCH that only sends `body` still has
        to be checked against the format the page *already* has, and a PATCH
        that only sends `content_format` against the body it already has.
        See .custom_html for what the two gates are and why the sandbox, not
        these, is the actual security control.
        """
        content_format = attrs.get(
            "content_format",
            self.instance.content_format if self.instance else ContentFormat.MARKDOWN,
        )
        if content_format != ContentFormat.HTML:
            return attrs
        if not organization_allows_custom_html(self._organization()):
            raise serializers.ValidationError(
                {
                    "content_format": "Custom HTML pages aren't enabled for this "
                    "organization."
                }
            )
        body = attrs.get("body", self.instance.body if self.instance else "")
        limit = max_html_bytes()
        if len((body or "").encode("utf-8")) > limit:
            raise serializers.ValidationError(
                {"body": f"That's larger than the {limit // 1024} KB limit for a custom-HTML page."}
            )
        return attrs

    def validate_property(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        if request is not None:
            # This also enforces property-scoped roles (not just the org
            # boundary) — validate_property runs on every write, so
            # (unlike PageViewSet.perform_create's own check, which only
            # runs on create) this is what catches a scoped member trying
            # to PATCH a page onto a property outside their own scope.
            # See /docs/open-questions.md, "Property-scoped role
            # enforcement".
            from apps.accounts.org_scoping import get_active_membership, property_accessible

            membership = get_active_membership(request.user)
            if not property_accessible(membership, value):
                raise serializers.ValidationError("That property isn't accessible to you.")
            return value
        # No request in context (e.g. constructed directly rather than via
        # PageViewSet) — fall back to the org-only check via the explicit
        # `organization` context PageViewSet.get_serializer_context sets.
        organization = self.context.get("organization")
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
