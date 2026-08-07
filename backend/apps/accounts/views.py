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
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Membership, Organization, Property, User
from .org_scoping import OrganizationScopedViewSet, get_active_membership
from .serializers import MembershipSerializer, PropertySerializer, UserSerializer


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
