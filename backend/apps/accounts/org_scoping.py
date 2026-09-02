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
# model) is enforced via scoped_property_ids/property_accessible below,
# not here — this table is only ever about the role rank itself.
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


def scoped_property_ids(membership):
    """`None` means this membership has account-wide access to every
    Property in its Organization (an empty `Membership.properties` — see
    that field's own help_text); otherwise the set of Property ids it's
    limited to. Shared by every queryset/serializer below that needs to
    actually enforce property-scoped roles (Property, Activity, Sighting)
    rather than just store the scope — see /docs/open-questions.md,
    "Property-scoped role enforcement"."""
    if membership is None:
        return set()
    ids = set(membership.properties.values_list("id", flat=True))
    return ids or None


def property_accessible(membership, property_obj):
    """True if `membership` can read/write `property_obj` at all: same
    organization, and — if this membership is scoped to specific
    properties — `property_obj` is one of them. `property_obj` may be
    None (e.g. Sighting's optional property FK); that's never accessible
    to a *scoped* membership (nothing to scope it to), but is left to the
    caller to decide for an account-wide one."""
    if membership is None or property_obj is None:
        return False
    if property_obj.organization_id != membership.organization_id:
        return False
    ids = scoped_property_ids(membership)
    return ids is None or property_obj.id in ids


def ensure_property_accessible(membership, property_obj):
    """Like property_accessible, but raises — for the function-based views
    (photo upload/delete, links, activity-species) that look a record up
    directly rather than going through a ViewSet's filtered queryset. Only
    for a Property FK that's *required* on its model (Activity) — see
    ensure_optional_property_accessible below for Sighting's, which is
    optional and needs different None handling."""
    if not property_accessible(membership, property_obj):
        raise PermissionDenied("That property isn't accessible to you.")


def ensure_optional_property_accessible(membership, property_obj):
    """Like ensure_property_accessible, but for a record whose Property FK
    is optional and nullable (Sighting) and whose organization has
    *already* been checked (e.g. via get_object_or_404(organization=...))
    — an account-wide membership can reach it either way, with or without
    a property; a property-scoped membership only if it has one and that
    property is in scope. (property_accessible itself always treats a
    None property as inaccessible, which is right for a *scoped*
    membership but wrong here for an account-wide one — this is the
    version that gets that distinction right.)"""
    ids = scoped_property_ids(membership)
    if ids is None:
        return
    if property_obj is None or property_obj.id not in ids:
        raise PermissionDenied("That record isn't accessible to you.")


def filter_by_property_scope(queryset, membership, *, property_field="property"):
    """Applies scoped_property_ids to a queryset that's already been
    filtered to the caller's organization. `property_field` is the FK
    field name pointing at Property — Activity/Sighting/Page all have a
    `property` FK (the default); PropertyViewSet itself passes `"id"`,
    since a Property *is* the thing being scoped, not a field pointing at
    one. For an optional FK (Sighting/Page), a row with no property at all
    is invisible to a scoped membership (there's nothing to check it
    against) even though an account-wide membership still sees it."""
    ids = scoped_property_ids(membership)
    if ids is None:
        return queryset
    lookup = property_field if property_field == "id" else f"{property_field}_id"
    return queryset.filter(**{f"{lookup}__in": ids})


def is_property_scoped(membership):
    """True if this membership's reach is limited to specific properties
    rather than being account-wide. The inverse of "account-wide", which is
    what an empty `Membership.properties` means everywhere else in here."""
    return scoped_property_ids(membership) is not None


def membership_manageable(acting_membership, target_membership):
    """Whether an admin (`acting_membership`) may act on `target_membership`
    through the org admin console — the *membership* counterpart to
    property_accessible above.

    An account-wide admin manages everyone in their organization, unchanged.
    A property-scoped admin's admin-level reach is narrowed (owner decision,
    2026-09-02 — see /docs/open-questions.md, "Accounts, orgs, and
    permissions") to members whose own scope is **non-empty and entirely
    within the admin's own**. Two consequences worth stating explicitly,
    because both are deliberate rather than incidental:

    * An **account-wide** member (empty scope) is never manageable by a
      property-scoped admin — their access reaches properties the admin
      itself can't see, so editing/removing them would let a scoped admin
      change access it doesn't hold. That also means a property-scoped
      admin structurally can't reach the org's account-wide admins.
    * **Partial overlap doesn't count.** If the admin manages property A
      and the target member is scoped to A *and* B, the target is out of
      reach — acting on them would affect their access to B. Full
      containment, not intersection, is the test.
    """
    if acting_membership is None or target_membership is None:
        return False
    if target_membership.organization_id != acting_membership.organization_id:
        return False
    admin_ids = scoped_property_ids(acting_membership)
    if admin_ids is None:
        return True
    target_ids = scoped_property_ids(target_membership)
    if target_ids is None:
        return False
    return target_ids <= admin_ids


def scope_assignable(acting_membership, property_ids):
    """Whether `acting_membership` may set `property_ids` as some other
    member's (or invitation's) property scope. An account-wide admin can
    assign anything, including an empty scope (= account-wide). A
    property-scoped admin can only assign a non-empty subset of its own
    scope: it can't hand out access it doesn't itself have, and it can't
    create an account-wide member (which would outrank the admin creating
    it)."""
    admin_ids = scoped_property_ids(acting_membership)
    if admin_ids is None:
        return True
    return bool(property_ids) and set(property_ids) <= admin_ids


def ensure_account_wide_admin(membership):
    """For org-level admin actions with no property dimension at all —
    renaming the organization, its public URL slug, its own theme. A
    property-scoped admin administers *its properties*, not the
    organization itself (owner decision, 2026-09-02), so those stay with
    account-wide admins."""
    if membership is None or not role_at_least(membership.role, Membership.Role.ADMIN):
        raise PermissionDenied("This action requires the 'admin' role or higher.")
    if is_property_scoped(membership):
        raise PermissionDenied(
            "This action is for organization-wide admins — your admin role is "
            "limited to specific properties."
        )


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
