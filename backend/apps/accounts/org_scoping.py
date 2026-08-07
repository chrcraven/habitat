"""
Shared "which organization is this request acting as" logic.

Phase 1 simplification: a user's *first* Membership is treated as their
active organization context. The data model already supports a user
belonging to multiple Organizations (see models.py), but nothing in Phase 1
needs an org switcher yet — the author's own account has exactly one. If a
second org shows up (e.g. the author joins someone else's account too),
this is the place to add real org-switching rather than the fixed
"first membership wins" behavior below.
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.viewsets import ModelViewSet


def get_active_membership(user):
    return user.memberships.select_related("organization").first()


class OrganizationScopedViewSet(ModelViewSet):
    """Base for viewsets whose data belongs to the caller's active
    Organization. Subclasses set `queryset`/`serializer_class` as usual;
    this handles filtering reads and stamping the org on create.

    `organization_field` is the model field name pointing at Organization —
    override it for models where that isn't `organization` (there aren't
    any yet).
    """

    organization_field = "organization"

    def get_organization(self):
        membership = get_active_membership(self.request.user)
        if membership is None:
            raise PermissionDenied(
                "You are not a member of any organization yet."
            )
        return membership.organization

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(**{self.organization_field: self.get_organization()})

    def perform_create(self, serializer):
        serializer.save(**{self.organization_field: self.get_organization()})
