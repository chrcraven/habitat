"""
Authoring/management API for Page — session-authenticated, editor+ to
write (see OrganizationRolePermission), viewer+ to read; same role
convention as every other org-scoped resource. The public site never hits
this — see apps/public_site/views.py for the AllowAny read surface a
visitor actually gets.

Listing: `GET /api/pages/` returns this org's **org-level** pages
(property is null) by default; `GET /api/pages/?property=<id>` returns
just that property's pages instead. There's no single endpoint that lists
"everything" — the org admin portal and a property's own page both only
ever need their own scope's pages.
"""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.accounts.models import Property
from apps.accounts.org_scoping import OrganizationScopedViewSet

from .models import Page
from .serializers import PageSerializer


class PageViewSet(OrganizationScopedViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # The `?property=` scoping below only applies to `list` — a
        # detail URL (`/api/pages/<id>/`, used by retrieve/update/
        # destroy) already identifies an exact page, org-level or
        # property-scoped, and must resolve regardless of that query
        # param being absent (or naming a *different* property than the
        # one this particular page happens to belong to).
        if self.action != "list":
            return qs
        property_id = self.request.query_params.get("property")
        if property_id is not None:
            # 404s (via the property lookup, not a queryset filter that
            # would just quietly return nothing) if that property isn't in
            # this org — same "don't confirm what's behind a cross-org id"
            # posture used elsewhere.
            property_ = get_object_or_404(
                Property, pk=property_id, organization=self.get_organization()
            )
            return qs.filter(property=property_)
        return qs.filter(property__isnull=True)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["organization"] = self.get_organization()
        return context

    def perform_create(self, serializer):
        organization = self.get_organization()
        property_ = serializer.validated_data.get("property")
        if property_ is not None and property_.organization_id != organization.id:
            raise ValidationError({"property": "That property isn't in your organization."})
        serializer.save(organization=organization, created_by=self.request.user)
