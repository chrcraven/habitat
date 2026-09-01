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
from apps.accounts.org_scoping import (
    OrganizationScopedViewSet,
    filter_by_property_scope,
    get_active_membership,
    scoped_property_ids,
)

from .models import Page
from .serializers import PageSerializer


class PageViewSet(OrganizationScopedViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Property-scoped roles (see /docs/open-questions.md,
        # "Property-scoped role enforcement") — a scoped membership only
        # ever sees property-level pages for its own properties; org-level
        # pages (property is null) aren't scoped to any property, so a
        # scoped membership never sees or authors those, same as it can't
        # do org-wide things like renaming the org itself.
        qs = filter_by_property_scope(qs, get_active_membership(self.request.user))
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
        # The property's own org membership *and* property-scope are both
        # already enforced by PageSerializer.validate_property (it runs
        # before perform_create, as part of is_valid()) whenever `property`
        # is set. The one thing that can't be caught there is the opposite
        # case — an org-level page (property left unset) — since
        # validate_property never even runs on a None value; block that
        # here for a property-scoped membership, same reasoning as
        # PropertyViewSet.perform_create not letting it create a brand-new
        # Property: an org-level page isn't scoped to any property at all.
        property_ = serializer.validated_data.get("property")
        if property_ is None and scoped_property_ids(get_active_membership(self.request.user)) is not None:
            raise ValidationError(
                {"property": "Your role is scoped to specific properties — choose one."}
            )
        serializer.save(organization=self.get_organization(), created_by=self.request.user)
