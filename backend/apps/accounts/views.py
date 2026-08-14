"""
Auth endpoints (signup/login/logout/me) plus the Property API.

Auth is session-based (decided — email/password, see /docs/roadmap.md
Phase 1), which means the SPA needs a CSRF token before it can POST. Flow:
GET /api/auth/csrf/ once to receive the csrftoken cookie, then send its
value back as the `X-CSRFToken` header on login/signup/logout and on any
viewset write. See frontend/src/api/client.ts for the client side of this.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, Organization, Property, User
from .org_scoping import OrganizationScopedViewSet, ensure_role, get_active_membership
from .serializers import (
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
    resolves "scope users/roles per org" (see /CLAUDE.md task log): an
    admin adds a member by setting their initial password directly
    (decided over a real email-invite flow, since no email backend is
    configured yet — the person shares that password out of band and can
    change it after logging in) and can scope their role to specific
    properties via Membership.properties, which existed on the model from
    Phase 1 but had no reachable UI until now.

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
        else:
            password = request.data.get("password") or ""
            try:
                validate_password(password)
            except DjangoValidationError as exc:
                return Response({"detail": " ".join(exc.messages)}, status=400)

        with transaction.atomic():
            user = existing_user or User.objects.create_user(
                email=email,
                password=request.data.get("password") or "",
                first_name=(request.data.get("first_name") or "").strip(),
                last_name=(request.data.get("last_name") or "").strip(),
            )
            membership = Membership.objects.create(
                user=user, organization=organization, role=role
            )
            membership.properties.set(properties)

        return Response(MembershipDetailSerializer(membership).data, status=201)

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
