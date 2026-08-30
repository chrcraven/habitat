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

    class Meta:
        model = Page
        fields = ["id", "title", "slug", "body_html", "updated_at"]

    def get_body_html(self, obj):
        return render_page_body(obj.body)
