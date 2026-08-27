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
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .invitations import send_invitation_email
from .models import Invitation, Membership, Organization, PasswordResetToken, Property, User
from .org_scoping import OrganizationScopedViewSet, ensure_role, get_active_membership
from .password_reset import send_password_reset_email
from .serializers import (
    InvitationSerializer,
    MembershipDetailSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    PropertySerializer,
    UserSerializer,
)


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
    queryset = Property.objects.all()
    serializer_class = PropertySerializer


def _admin_count(organization):
    return Membership.objects.filter(
        organization=organization, role=Membership.Role.ADMIN
    ).count()


class OrganizationDetailView(APIView):
    """GET/PATCH the caller's active Organization — today just its name.
    This is the org admin portal's "org settings" half (see /CLAUDE.md
    task log); member/role management is MembershipViewSet below. PATCH
    requires admin; any member can GET (so the org name can be shown
    read-only elsewhere without an extra permission check)."""

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
        ensure_role(request.user, Membership.Role.ADMIN)
        serializer = OrganizationSerializer(
            membership.organization, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


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
    """

    def _organization(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            raise PermissionDenied("You are not a member of any organization yet.")
        return membership.organization

    def list(self, request):
        organization = self._organization(request)
        memberships = (
            Membership.objects.filter(organization=organization)
            .select_related("user")
            .prefetch_related("properties")
            .order_by("user__email")
        )
        return Response(MembershipDetailSerializer(memberships, many=True).data)

    def create(self, request):
        organization = self._organization(request)
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
        ensure_role(request.user, Membership.Role.ADMIN)
        membership = get_object_or_404(Membership, id=pk, organization=organization)

        role = request.data.get("role")
        if role is not None:
            if role not in Membership.Role.values:
                return Response({"detail": "Invalid role."}, status=400)
            demoting_last_admin = (
                membership.role == Membership.Role.ADMIN
                and role != Membership.Role.ADMIN
                and _admin_count(organization) <= 1
            )
            if demoting_last_admin:
                return Response(
                    {"detail": "This organization needs at least one admin."}, status=400
                )
            membership.role = role

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
            membership.properties.set(properties)

        membership.save()
        return Response(MembershipDetailSerializer(membership).data)

    def destroy(self, request, pk=None):
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        membership = get_object_or_404(Membership, id=pk, organization=organization)
        if membership.role == Membership.Role.ADMIN and _admin_count(organization) <= 1:
            return Response(
                {"detail": "This organization needs at least one admin."}, status=400
            )
        membership.delete()
        return Response(status=204)


class InvitationViewSet(viewsets.ViewSet):
    """The admin-only "Pending invitations" list on the org admin portal —
    lets an admin see who's been invited but hasn't joined yet, and revoke
    an invitation (e.g. sent to the wrong address, or no longer wanted).
    Creating an invitation happens through MembershipViewSet.create, not
    here — "add a member" is one form either way, it's just the *result*
    that differs by whether the email already has an account."""

    def _organization(self, request):
        membership = get_active_membership(request.user)
        if membership is None:
            raise PermissionDenied("You are not a member of any organization yet.")
        return membership.organization

    def list(self, request):
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        invitations = (
            Invitation.objects.filter(organization=organization, accepted_at__isnull=True)
            .select_related("invited_by")
            .prefetch_related("properties")
        )
        return Response(InvitationSerializer(invitations, many=True).data)

    def destroy(self, request, pk=None):
        organization = self._organization(request)
        ensure_role(request.user, Membership.Role.ADMIN)
        invitation = get_object_or_404(Invitation, id=pk, organization=organization)
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
        invitation = get_object_or_404(Invitation, id=pk, organization=organization)
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
