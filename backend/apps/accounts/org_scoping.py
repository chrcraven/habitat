"""
Shared "which organization is this request acting as, and what is the
caller allowed to do" logic.

Phase 1 simplification: a user's *first* Membership is treated as their
active organization context. The data model already supports a user
belonging to multiple Organizations (see models.py), but nothing in Phase 1
needs an org switcher yet — the author's own account has exactly one. If a
second org shows up (e.g. the author joins someone else's account too),
this is the place to add real org-switching rather than the fixed
"first membership wins" behavior below.
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.viewsets import ModelViewSet

from .models import Membership


def get_active_membership(user):
    return user.memberships.select_related("organization").first()


# Role capabilities (see the Membership.role field docstring and
# /docs/open-questions.md, "Exact role definitions" — this resolves the
# CRUD half of that question for Phase 1): viewer = read only,
# editor = read/create/update, admin = also delete. Property-level role
# scoping (a role limited to specific properties, also part of the decided
# model) isn't enforced yet — every membership here is account-wide; add it
# alongside a real invite/role-management UI (Phase 3) rather than here.
_ROLE_RANK = {
    Membership.Role.VIEWER: 0,
    Membership.Role.EDITOR: 1,
    Membership.Role.ADMIN: 2,
}


def role_at_least(role, minimum):
    return _ROLE_RANK.get(role, -1) >= _ROLE_RANK[minimum]


def ensure_role(user, minimum):
    """For the handful of endpoints (photo upload) that aren't a
    ModelViewSet and so don't go through OrganizationRolePermission —
    raises PermissionDenied instead of returning a bool so callers don't
    have to remember to check it."""
    membership = get_active_membership(user)
    if membership is None or not role_at_least(membership.role, minimum):
        raise PermissionDenied(f"This action requires the '{minimum}' role or higher.")


class OrganizationRolePermission(BasePermission):
    """Read (GET/HEAD/OPTIONS) requires any membership; create/update
    require editor+; delete requires admin. Combined with
    OrganizationScopedViewSet's queryset filtering, which is what actually
    keeps one org's data from another's — this only gates *what a member
    of the right org* is allowed to do to it.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        membership = get_active_membership(request.user)
        if membership is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        minimum = Membership.Role.ADMIN if request.method == "DELETE" else Membership.Role.EDITOR
        return role_at_least(membership.role, minimum)


class OrganizationScopedViewSet(ModelViewSet):
    """Base for viewsets whose data belongs to the caller's active
    Organization. Subclasses set `queryset`/`serializer_class` as usual;
    this handles filtering reads, stamping the org on create, and role
    enforcement via OrganizationRolePermission.

    `organization_field` is the model field name pointing at Organization —
    override it for models where that isn't `organization` (there aren't
    any yet).
    """

    organization_field = "organization"
    permission_classes = [OrganizationRolePermission]

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


def filter_is_public(queryset, request):
    """Shared `?is_public=true|false` filter for Activity/Sighting
    querysets — the frontend's default record view shows public records
    only (see PropertyMapPage), with a toggle to include private ones.
    This is about visibility *within your own org's app*, not the
    unauthenticated public page (that's Phase 2 — is_public just decides
    what *that page* will show once it exists)."""
    raw = request.query_params.get("is_public")
    if raw is None:
        return queryset
    return queryset.filter(is_public=raw.lower() == "true")
