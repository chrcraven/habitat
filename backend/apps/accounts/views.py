"""
Auth endpoints (signup/login/logout/me) plus the Property API.

Auth is session-based (decided — email/password, see /docs/roadmap.md
Phase 1), which means the SPA needs a CSRF token before it can POST. Flow:
GET /api/auth/csrf/ once to receive the csrftoken cookie, then send its
value back as the `X-CSRFToken` header on login/signup/logout and on any
viewset write. See frontend/src/api/client.ts for the client side of this.
"""

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, parser_classes, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .invitations import send_invitation_email
from .models import Invitation, Membership, Organization, PasswordResetToken, Property, User
from .org_scoping import (
    OrganizationScopedViewSet,
    ensure_account_wide_admin,
    ensure_role,
    filter_by_property_scope,
    get_active_membership,
    is_property_scoped,
    membership_manageable,
    scope_assignable,
    scoped_property_ids,
)
from .password_reset import send_password_reset_email
from .serializers import (
    DeletedPropertySerializer,
    InvitationSerializer,
    MembershipDetailSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    PropertySerializer,
    UserSerializer,
)
from .theming import MAX_THEME_IMAGE_BYTES


def _session_payload(user):
    membership = get_active_membership(user)
    return {
        "user": UserSerializer(user).data,
        "membership": MembershipSerializer(membership).data if membership else None,
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    """Visited once on app load so the browser has a csrftoken cookie to
    echo back on the first real POST."""
    get_token(request)
    return Response({"detail": "CSRF cookie set"})


@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    """Creates a brand-new account: a User, an Organization named after
    them (renamable later — no org-settings UI yet), and an admin
    Membership tying the two together. This is the "solo homeowner" path
    through the decided one-account-always-an-org model — see
    /docs/data-model-notes.md.
    """
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    organization_name = (request.data.get("organization_name") or "").strip()

    if not email:
        return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response(
            {"detail": "An account with that email already exists."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=(request.data.get("first_name") or "").strip(),
            last_name=(request.data.get("last_name") or "").strip(),
        )
        organization = Organization.objects.create(
            name=organization_name or f"{email}'s land"
        )
        Membership.objects.create(
            user=user, organization=organization, role=Membership.Role.ADMIN
        )

    login(request, user)
    return Response(_session_payload(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    email = (request.data.get("email") or "").strip().lower()
    password = request.data.get("password") or ""
    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED
        )
    login(request, user)
    return Response(_session_payload(user))


@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def me(request):
    return Response(_session_payload(request.user))


@api_view(["POST"])
def change_password(request):
    """Self-service password change (resolves the "member can't change
    their own password yet" gap in open-questions.md — an admin-added
    member's only option used to be asking the admin who set their
    initial password to set a new one). Requires the caller's *current*
    password, same as any "change password" flow, so a hijacked but not
    yet logged-out session can't be used to lock the real owner out.
    `update_session_auth_hash` keeps the current session valid after
    `set_password` changes the hash it's keyed on — without it, this
    request would log the user out mid-response.
    """
    current_password = request.data.get("current_password") or ""
    new_password = request.data.get("new_password") or ""

    if not request.user.check_password(current_password):
        return Response({"detail": "Current password is incorrect."}, status=400)
    try:
        validate_password(new_password, user=request.user)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=400)

    request.user.set_password(new_password)
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return Response({"detail": "Password updated."})


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    """"Forgot password" — start of the flow (see .password_reset and
    .models.PasswordResetToken). Always returns the same generic 200
    regardless of whether the email actually has an account, so this
    endpoint can't be used to enumerate registered addresses; if it does,
    a fresh token is emailed (best-effort — see send_password_reset_email)
    and any previous unused tokens for that user are cleared out so an
    old, possibly-forwarded link stops working once a newer one is
    requested.
    """
    email = (request.data.get("email") or "").strip().lower()
    user = User.objects.filter(email=email).first() if email else None
    if user is not None:
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).delete()
        reset = PasswordResetToken.objects.create(user=user)
        send_password_reset_email(reset)
    return Response(
        {"detail": "If an account exists for that email, a reset link has been sent."}
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Second half of the flow — sets a new password from a token minted
    by password_reset_request above. A bad, already-used, or expired
    token all get the same generic error (same "don't confirm what's
    behind an opaque token" stance as the invitation flow), and a
    successful reset logs the user in immediately, matching signup/
    invitation-accept's "create the session in the same response"
    convention rather than bouncing them to a separate login step.
    """
    token = request.data.get("token") or ""
    new_password = request.data.get("new_password") or ""

    reset = PasswordResetToken.objects.filter(token=token, used_at__isnull=True).first()
    if reset is None or reset.is_expired:
        return Response(
            {"detail": "That reset link is invalid or has expired."}, status=400
        )
    try:
        validate_password(new_password, user=reset.user)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=400)

    with transaction.atomic():
        reset.user.set_password(new_password)
        reset.user.save(update_fields=["password"])
        reset.used_at = timezone.now()
        reset.save(update_fields=["used_at"])

    login(request, reset.user)
    return Response(_session_payload(reset.user))


class PropertyViewSet(OrganizationScopedViewSet):
    """Standard org-scoped CRUD (see org_scoping.py), plus soft delete
    (decided 2026-08-29 — see /docs/open-questions.md, "Soft delete"):
    DELETE doesn't remove the row, it sets `deleted_at` (perform_destroy
    below), which the default `Property.objects` manager then hides from
    every normal queryset — including this viewset's own list/retrieve,
    the public site, and Activity/Sighting's own querysets (see
    apps/activities/views.py, apps/sightings/views.py). `deleted`/`restore`
    below are admin-only ("also delete" already covers destroy; restore is
    the same trust level) and use `Property.all_objects` since the default
    manager can't see a deleted row to restore it.

    Also enforces property-scoped roles (`Membership.properties`, decided
    since Phase 1 but not actually enforced until now — see
    /docs/open-questions.md, "Property-scoped role enforcement"): a scoped
    membership's list/retrieve/update/delete are all limited to its own
    properties (get_queryset), and it can't create a brand-new Property at
    all (perform_create) — a new property isn't scoped to anyone yet, and
    letting a scoped member create one would hand them an unscoped escape
    hatch around their own restriction. Creating properties stays an
    account-wide action; only an unscoped editor/admin (the common case —
    property scoping is meant to *restrict* an existing member to part of
    the account, not to be everyone's normal path) can do it.
    """

    queryset = Property.objects.all()
    serializer_class = PropertySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_by_property_scope(
            qs, get_active_membership(self.request.user), property_field="id"
        )

    def perform_create(self, serializer):
        membership = get_active_membership(self.request.user)
        if scoped_property_ids(membership) is not None:
            raise PermissionDenied(
                "Your role is scoped to specific properties, so you can't "
                "create a new one — ask an org admin to create it and add "
                "you to it."
            )
        super().perform_create(serializer)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])

    @action(detail=False, methods=["get"])
    def deleted(self, request):
        """The org admin portal's "Recently deleted" list — soft-deleted
        properties still inside their 30-day restore window, newest first.
        Scoped the same way as the main queryset above: a property-scoped
        admin only sees (and can restore) properties in their own scope."""
        ensure_role(request.user, Membership.Role.ADMIN)
        properties = (
            Property.all_objects.deleted()
            .filter(organization=self.get_organization())
            .order_by("-deleted_at")
        )
        properties = filter_by_property_scope(
            properties, get_active_membership(request.user), property_field="id"
        )
        return Response(DeletedPropertySerializer(properties, many=True).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Clears `deleted_at`, making the property (and everything that
        was hidden alongside it — its activities/sightings, per the
        decided cascade behavior) visible again everywhere it was hidden
        from. 404s for a property outside the caller's org, one outside a
        scoped admin's own property scope, or one that isn't actually
        deleted — same "don't confirm what's behind an ID" posture as
        everywhere else."""
        ensure_role(request.user, Membership.Role.ADMIN)
        qs = Property.all_objects.deleted().filter(organization=self.get_organization())
        qs = filter_by_property_scope(qs, get_active_membership(request.user), property_field="id")
        property_ = get_object_or_404(qs, pk=pk)
        property_.deleted_at = None
        property_.save(update_fields=["deleted_at"])
        return Response(PropertySerializer(property_, context={"request": request}).data)


def _account_wide_admin_count(organization):
    """Admins whose role *isn't* limited to specific properties — the ones
    who can still rename the organization and manage account-wide members
    now that a property-scoped admin's reach is narrowed to its own
    properties (see org_scoping.membership_manageable). This, not the raw
    admin count, is what the lockout guards below protect: an organization
    left with only property-scoped admins can't administer *itself* any
    more, and nothing in the app can recover from that."""
    return (
        Membership.objects.filter(
            organization=organization,
            role=Membership.Role.ADMIN,
            properties__isnull=True,
        )
        .distinct()
        .count()
    )


class OrganizationDetailView(APIView):
    """GET/PATCH the caller's active Organization — today just its name.
    This is the org admin portal's "org settings" half (see /CLAUDE.md
    task log); member/role management is MembershipViewSet below. PATCH
    requires an *account-wide* admin (renaming the org, its public slug and
    its theme have no property dimension to scope, so they aren't a
    property-scoped admin's to change — owner decision 2026-09-02); any
    member can GET (so the org name can be shown read-only elsewhere
    without an extra permission check)."""

    def get(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            return Response(
                {"detail": "You are not a member of any organization yet."}, status=404
            )
        return Response(OrganizationSerializer(membership.organization).data)

    def patch(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            return Response(
                {"detail": "You are not a member of any organization yet."}, status=404
            )
        ensure_account_wide_admin(membership)
        serializer = OrganizationSerializer(
            membership.organization, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# --- Public-site theme header image ---------------------------------------
#
# One decorative banner image per org/property (not a gallery), part of the
# "constrained theme controls" feature (see apps/accounts/theming.py and
# /docs/open-questions.md, "Public site storytelling / custom content").
# GET is session-cookie authenticated (any member — same as an activity/
# sighting photo) so the admin UI can preview it while editing, even for a
# still-private property; the actual public-site rendering fetches the
# *unauthenticated* copy at apps/public_site/views.py's equivalent endpoint
# instead. POST (multipart, field name `image`) replaces it; DELETE clears
# it back to "no header image" (falls back to the default/inherited theme).


@api_view(["GET", "POST", "DELETE"])
@parser_classes([MultiPartParser])
def organization_theme_image(request):
    membership = get_active_membership(request.user)
    if membership is None:
        return Response(
            {"detail": "You are not a member of any organization yet."}, status=404
        )
    organization = membership.organization

    if request.method == "GET":
        if not organization.theme_header_image_content_type:
            return Response(status=404)
        return HttpResponse(
            bytes(organization.theme_header_image),
            content_type=organization.theme_header_image_content_type,
        )

    ensure_role(request.user, Membership.Role.EDITOR)
    # The org's own banner is an org-level asset with no property to scope
    # it to, so it goes the same way as org rename/slug/theme above: a
    # property-scoped member edits its *properties'* theming, not the
    # organization's (owner decision, 2026-09-02).
    if is_property_scoped(membership):
        raise PermissionDenied(
            "Your role is limited to specific properties — set a header image on one "
            "of your own properties instead."
        )

    if request.method == "DELETE":
        organization.theme_header_image = None
        organization.theme_header_image_content_type = ""
        organization.save(
            update_fields=["theme_header_image", "theme_header_image_content_type"]
        )
        return Response(status=204)

    image = request.FILES.get("image")
    if not image:
        return Response({"detail": "No image file provided."}, status=400)
    if not (image.content_type or "").startswith("image/"):
        return Response({"detail": "Only image uploads are supported."}, status=400)
    if image.size > MAX_THEME_IMAGE_BYTES:
        return Response({"detail": "Image is too large (max 5MB)."}, status=400)
    organization.theme_header_image = image.read()
    organization.theme_header_image_content_type = image.content_type
    organization.save(
        update_fields=["theme_header_image", "theme_header_image_content_type"]
    )
    return Response(OrganizationSerializer(organization).data)


@api_view(["GET", "POST", "DELETE"])
@parser_classes([MultiPartParser])
def property_theme_image(request, pk):
    """Mirror of organization_theme_image above, for one property's own
    header image. 404s for a property outside the caller's org or outside
    a property-scoped membership's own scope, same scoping as the
    property API (PropertyViewSet)."""
    membership = get_active_membership(request.user)
    if membership is None:
        return Response(
            {"detail": "You are not a member of any organization yet."}, status=404
        )
    qs = Property.objects.filter(organization=membership.organization)
    ids = scoped_property_ids(membership)
    if ids is not None:
        qs = qs.filter(id__in=ids)
    property_ = get_object_or_404(qs, pk=pk)

    if request.method == "GET":
        if not property_.theme_header_image_content_type:
            return Response(status=404)
        return HttpResponse(
            bytes(property_.theme_header_image),
            content_type=property_.theme_header_image_content_type,
        )

    ensure_role(request.user, Membership.Role.EDITOR)

    if request.method == "DELETE":
        property_.theme_header_image = None
        property_.theme_header_image_content_type = ""
        property_.save(
            update_fields=["theme_header_image", "theme_header_image_content_type"]
        )
        return Response(status=204)

    image = request.FILES.get("image")
    if not image:
        return Response({"detail": "No image file provided."}, status=400)
    if not (image.content_type or "").startswith("image/"):
        return Response({"detail": "Only image uploads are supported."}, status=400)
    if image.size > MAX_THEME_IMAGE_BYTES:
        return Response({"detail": "Image is too large (max 5MB)."}, status=400)
    property_.theme_header_image = image.read()
    property_.theme_header_image_content_type = image.content_type
    property_.save(
        update_fields=["theme_header_image", "theme_header_image_content_type"]
    )
    return Response(PropertySerializer(property_, context={"request": request}).data)


# --- Public-URL QR codes -------------------------------------------------
#
# Both endpoints accept a `base_url` form field (the public-site origin, as
# the browser sees it — the backend can't infer it since the SPA is served
# from a different origin) and an optional `logo` image file, and return an
# image/png of a QR code pointing at the org/property's own public page. Any
# member can generate one (it exposes nothing that isn't already on the
# public site); a viewer downloading a shareable code is harmless. See
# apps/accounts/qrcodes.py.


def _qr_response(request, public_path):
    from .qrcodes import make_qr_png, public_base_url

    try:
        base = public_base_url(request.data.get("base_url"))
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    logo = request.FILES.get("logo")
    logo_bytes = logo.read() if logo else None
    try:
        png = make_qr_png(f"{base}{public_path}", logo_bytes=logo_bytes)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    response = HttpResponse(png, content_type="image/png")
    response["Content-Disposition"] = 'inline; filename="habitat-qr.png"'
    return response


@api_view(["POST"])
def organization_qr_code(request):
    """QR code for the caller's org portfolio page (`/public/<org-slug>`)."""
    membership = get_active_membership(request.user)
    if membership is None:
        return Response(
            {"detail": "You are not a member of any organization yet."}, status=404
        )
    return _qr_response(request, f"/public/{membership.organization.slug}")


@api_view(["POST"])
def property_qr_code(request, pk):
    """QR code for one property's public page
    (`/public/<org-slug>/<property-slug>`). 404s for a property outside the
    caller's org — or outside a property-scoped membership's own scope,
    same as property_theme_image and the property API itself."""
    membership = get_active_membership(request.user)
    if membership is None:
        return Response(
            {"detail": "You are not a member of any organization yet."}, status=404
        )
    qs = Property.objects.filter(organization=membership.organization)
    ids = scoped_property_ids(membership)
    if ids is not None:
        qs = qs.filter(id__in=ids)
    property_ = get_object_or_404(qs, pk=pk)
    return _qr_response(
        request, f"/public/{membership.organization.slug}/{property_.slug}"
    )


class MembershipViewSet(viewsets.ViewSet):
    """Org admin portal's member/role management — the mechanism that
    resolves "scope users/roles per org" (see /CLAUDE.md task log). Can
    scope a member's role to specific properties via Membership.properties,
    which existed on the model from Phase 1 but had no reachable UI until
    the org admin portal shipped.

    Adding a member by email now branches on whether that email already
    has a Habitat account: if it does, they're attached to this
    organization immediately (same as before — no invite step needed,
    they can already log in). If it's a brand-new email, this creates a
    pending Invitation and emails an accept link instead of the old
    "admin sets an initial password" flow — see InvitationViewSet and
    apps/accounts/invitations.py.

    Listing is open to any member of the org (so a viewer can at least see
    who's on the team); create/update/delete all require admin.

    A **property-scoped** admin's reach through here is narrowed to members
    within its own property scope (owner decision, 2026-09-02 — see
    org_scoping.membership_manageable for the exact containment rule and
    /docs/open-questions.md for the decision record). An account-wide
    admin's behavior is unchanged in every path below.
    """

    def _organization(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            raise PermissionDenied("You are not a member of any organization yet.")
        return membership.organization

    def _acting_membership(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            raise PermissionDenied("You are not a member of any organization yet.")
        return membership

    def _ensure_manageable(self, acting_membership, target_membership):
        if not membership_manageable(acting_membership, target_membership):
            raise PermissionDenied(
                "That member is outside the properties your admin role covers."
            )

    def list(self, request):
        organization = self._organization(request)
        acting = get_active_membership(request.user)
        memberships = (
            Membership.objects.filter(organization=organization)
            .select_related("user")
            .prefetch_related("properties")
            .order_by("user__email")
        )
        if (
            acting is not None
            and acting.role == Membership.Role.ADMIN
            and is_property_scoped(acting)
        ):
            # A property-scoped admin sees the members it can actually
            # manage, plus itself — a list full of rows whose every control
            # 403s reads as a bug rather than as a boundary. Filtered in
            # Python off the prefetched scope rather than in SQL: the test
            # is "every one of the target's properties is one of mine",
            # which a queryset filter can't express in one pass, and an
            # org's member list is small.
            admin_ids = scoped_property_ids(acting) or set()

            def visible(m):
                if m.id == acting.id:
                    return True
                target_ids = {p.id for p in m.properties.all()}
                return bool(target_ids) and target_ids <= admin_ids

            memberships = [m for m in memberships if visible(m)]
        return Response(MembershipDetailSerializer(memberships, many=True).data)

    def create(self, request):
        organization = self._organization(request)
        acting = self._acting_membership(request)
        ensure_role(request.user, Membership.Role.ADMIN)

        email = (request.data.get("email") or "").strip().lower()
        role = request.data.get("role")
        property_ids = request.data.get("properties") or []

        if not email:
            return Response({"detail": "Email is required."}, status=400)
        if role not in Membership.Role.values:
            return Response({"detail": "A valid role is required."}, status=400)

        properties = list(Property.objects.filter(organization=organization, id__in=property_ids))
        if len(properties) != len(set(property_ids)):
            return Response(
                {"detail": "One or more properties aren't part of this organization."},
                status=400,
            )
        # A property-scoped admin can add a member, but only inside its own
        # scope — never account-wide (an unscoped member outranks the admin
        # creating it) and never onto a property it doesn't manage.
        if not scope_assignable(acting, [p.id for p in properties]):
            raise PermissionDenied(
                "You can only add members scoped to the properties your admin role "
                "covers — pick at least one of your own properties."
            )

        existing_user = User.objects.filter(email=email).first()
        if existing_user is not None:
            if Membership.objects.filter(user=existing_user, organization=organization).exists():
                return Response(
                    {"detail": "That person is already a member of this organization."},
                    status=400,
                )
            with transaction.atomic():
                membership = Membership.objects.create(
                    user=existing_user, organization=organization, role=role
                )
                membership.properties.set(properties)
            return Response(MembershipDetailSerializer(membership).data, status=201)

        # No account with this email yet — invite rather than create the
        # account for them (see class docstring / apps/accounts/invitations.py).
        if Invitation.objects.filter(
            organization=organization, email=email, accepted_at__isnull=True
        ).exists():
            return Response(
                {"detail": "There's already a pending invitation for that email."},
                status=400,
            )

        with transaction.atomic():
            invitation = Invitation.objects.create(
                organization=organization, email=email, role=role, invited_by=request.user
            )
            invitation.properties.set(properties)
        send_invitation_email(invitation)

        return Response(InvitationSerializer(invitation).data, status=201)

    def partial_update(self, request, pk=None):
        organization = self._organization(request)
        acting = self._acting_membership(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        membership = get_object_or_404(Membership, id=pk, organization=organization)
        self._ensure_manageable(acting, membership)

        role = request.data.get("role")
        if role is not None and role not in Membership.Role.values:
            return Response({"detail": "Invalid role."}, status=400)

        properties = None
        if "properties" in request.data:
            property_ids = request.data.get("properties") or []
            properties = list(
                Property.objects.filter(organization=organization, id__in=property_ids)
            )
            if len(properties) != len(set(property_ids)):
                return Response(
                    {"detail": "One or more properties aren't part of this organization."},
                    status=400,
                )
            # Same rule as create: a property-scoped admin can move a member
            # around *within* its own scope, but can't widen that member
            # past it (or unscope them entirely, which would take them out
            # of the admin's reach for good).
            if not scope_assignable(acting, [p.id for p in properties]):
                raise PermissionDenied(
                    "You can only scope members to the properties your admin role "
                    "covers — pick at least one of your own properties."
                )

        # Lockout guard. The thing an organization can't afford to lose is
        # its last *account-wide* admin, not its last admin of any kind:
        # a property-scoped admin can't rename the org or manage
        # account-wide members, so an org left with only those has no way
        # back. Both fields can move a membership out of that state
        # independently (role away from admin, or scoping an account-wide
        # admin to specific properties), so compare before/after rather
        # than checking either field alone.
        was_account_wide_admin = (
            membership.role == Membership.Role.ADMIN and not membership.properties.exists()
        )
        final_role = role if role is not None else membership.role
        final_scoped = (
            bool(properties) if properties is not None else membership.properties.exists()
        )
        if (
            was_account_wide_admin
            and not (final_role == Membership.Role.ADMIN and not final_scoped)
            and _account_wide_admin_count(organization) <= 1
        ):
            return Response(
                {"detail": "This organization needs at least one organization-wide admin."},
                status=400,
            )

        if role is not None:
            membership.role = role
        if properties is not None:
            membership.properties.set(properties)

        membership.save()
        return Response(MembershipDetailSerializer(membership).data)

    def destroy(self, request, pk=None):
        organization = self._organization(request)
        acting = self._acting_membership(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        membership = get_object_or_404(Membership, id=pk, organization=organization)
        self._ensure_manageable(acting, membership)
        if (
            membership.role == Membership.Role.ADMIN
            and not membership.properties.exists()
            and _account_wide_admin_count(organization) <= 1
        ):
            return Response(
                {"detail": "This organization needs at least one organization-wide admin."},
                status=400,
            )
        membership.delete()
        return Response(status=204)


class InvitationViewSet(viewsets.ViewSet):
    """The admin-only "Pending invitations" list on the org admin portal —
    lets an admin see who's been invited but hasn't joined yet, and revoke
    an invitation (e.g. sent to the wrong address, or no longer wanted).
    Creating an invitation happens through MembershipViewSet.create, not
    here — "add a member" is one form either way, it's just the *result*
    that differs by whether the email already has an account.

    A pending invitation carries the same property scope its membership
    will have once accepted, so it follows the same narrowing a
    property-scoped admin gets in MembershipViewSet: it sees and can act on
    invitations inside its own scope only. Without that, a scoped admin
    could revoke (or re-send) an invitation to an account-wide member it
    can't touch once that person has actually joined."""

    def _organization(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            raise PermissionDenied("You are not a member of any organization yet.")
        return membership.organization

    def _in_scope(self, acting_membership, invitation):
        return scope_assignable(
            acting_membership, [p.id for p in invitation.properties.all()]
        )

    def _get_in_scope(self, request, organization, pk):
        invitation = get_object_or_404(Invitation, id=pk, organization=organization)
        if not self._in_scope(get_active_membership(request.user), invitation):
            raise PermissionDenied(
                "That invitation is outside the properties your admin role covers."
            )
        return invitation

    def list(self, request):
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        acting = get_active_membership(request.user)
        invitations = (
            Invitation.objects.filter(organization=organization, accepted_at__isnull=True)
            .select_related("invited_by")
            .prefetch_related("properties")
        )
        if is_property_scoped(acting):
            invitations = [inv for inv in invitations if self._in_scope(acting, inv)]
        return Response(InvitationSerializer(invitations, many=True).data)

    def destroy(self, request, pk=None):
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        invitation = self._get_in_scope(request, organization, pk)
        invitation.delete()
        return Response(status=204)

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        """Re-sends an invitation's email and refreshes its expiry clock
        (by bumping `created_at`, which `is_expired` measures from) so a
        link that expired before anyone used it works again from one
        click — previously the only fix for an expired invite was revoke
        it and fill out "add a member" again from scratch. Keeps the same
        token rather than minting a new one, since the invitee may
        already have the original link from the first send."""
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        invitation = self._get_in_scope(request, organization, pk)
        invitation.created_at = timezone.now()
        invitation.save(update_fields=["created_at"])
        send_invitation_email(invitation)
        return Response(InvitationSerializer(invitation).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def invitation_detail(request, token):
    """Looked up by the (unauthenticated) accept-invite page before it
    shows its form, so it can greet the invitee by org name/role rather
    than just asking for a password cold. A used or expired invitation
    404s, same "don't even confirm what's behind an ID" stance the public
    site takes (see apps/public_site/views.py)."""
    invitation = get_object_or_404(Invitation, token=token, accepted_at__isnull=True)
    if invitation.is_expired:
        return Response({"detail": "This invitation has expired."}, status=404)
    return Response(
        {
            "email": invitation.email,
            "organization_name": invitation.organization.name,
            "role": invitation.role,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def invitation_accept(request, token):
    """Creates the invitee's User + Membership together and logs them in —
    the "joining an existing org" counterpart to signup's "create a new
    org" (see .models.Invitation's docstring)."""
    invitation = get_object_or_404(Invitation, token=token, accepted_at__isnull=True)
    if invitation.is_expired:
        return Response({"detail": "This invitation has expired."}, status=400)
    if User.objects.filter(email=invitation.email).exists():
        return Response(
            {"detail": "An account with this email already exists — log in instead."},
            status=400,
        )

    password = request.data.get("password") or ""
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=400)

    with transaction.atomic():
        user = User.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=(request.data.get("first_name") or "").strip(),
            last_name=(request.data.get("last_name") or "").strip(),
        )
        membership = Membership.objects.create(
            user=user, organization=invitation.organization, role=invitation.role
        )
        membership.properties.set(invitation.properties.all())
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])

    login(request, user)
    return Response(_session_payload(user), status=201)
