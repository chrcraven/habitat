"""
Public-site shape for an authored Page — distinct from
apps/pages/serializers.py's PageSerializer (the authoring shape, which
exposes the raw markdown `body` for editing). A public visitor gets
`body_html` — already rendered and sanitized (see apps/pages/rendering.py)
— never the raw source, so there's exactly one place (this render step)
that has to get sanitization right rather than trusting every future
reader of `body` to re-sanitize it themselves.
"""

from rest_framework import serializers
from rest_framework.reverse import reverse

from apps.pages.custom_html import organization_allows_custom_html
from apps.pages.models import Page
from apps.pages.rendering import render_page_body


class PublicPageListSerializer(serializers.ModelSerializer):
    """Nav-list shape — title/slug only, no body (kept small since this is
    embedded in the org/property payload for every page load)."""

    class Meta:
        model = Page
        fields = ["id", "title", "slug"]


class PublicPageDetailSerializer(serializers.ModelSerializer):
    body_html = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "content_format", "body_html", "document_url", "updated_at"]

    def get_body_html(self, obj):
        """Sanitized HTML for a markdown page, safe to inline. Always empty
        for a custom-HTML page — that content is never inlined into the
        public site's own DOM; the visitor loads it as its own sandboxed
        document via `document_url` instead."""
        if obj.is_custom_html():
            return ""
        return render_page_body(obj.body)

    def get_document_url(self, obj):
        """Where a custom-HTML page's sandboxed document lives, or null —
        null both for an ordinary markdown page (nothing to frame) and for
        an HTML page whose organization has had custom content switched off
        (the per-tenant kill-switch), which is also what makes the document
        endpoint itself 404. Null is the frontend's signal to render an
        "unavailable" note rather than an empty frame."""
        if not obj.is_custom_html():
            return None
        if not organization_allows_custom_html(obj.organization):
            return None
        request = self.context.get("request")
        if obj.property_id:
            path = reverse(
                "public-property-page-document",
                kwargs={
                    "org_slug": obj.organization.slug,
                    "property_slug": obj.property.slug,
                    "page_slug": obj.slug,
                },
            )
        else:
            path = reverse(
                "public-organization-page-document",
                kwargs={"org_slug": obj.organization.slug, "page_slug": obj.slug},
            )
        return request.build_absolute_uri(path) if request else path
