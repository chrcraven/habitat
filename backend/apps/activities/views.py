from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.accounts.models import Membership
from apps.accounts.org_scoping import (
    OrganizationScopedViewSet,
    ensure_role,
    filter_is_public,
    get_active_membership,
)

from .models import Activity, ActivityPhoto, WorkflowState
from .serializers import ActivityPhotoSerializer, ActivitySerializer, WorkflowStateSerializer

MAX_PHOTO_BYTES = 8 * 1024 * 1024


class WorkflowStateViewSet(ReadOnlyModelViewSet):
    """Read-only: every Organization gets a default workflow seeded on
    creation (see signals.py). Editing the workflow is org-settings UI
    that doesn't exist yet — out of scope for Phase 1's logging flow."""

    serializer_class = WorkflowStateSerializer

    def get_queryset(self):
        membership = get_active_membership(self.request.user)
        if membership is None:
            return WorkflowState.objects.none()
        return WorkflowState.objects.filter(organization=membership.organization)


class ActivityViewSet(OrganizationScopedViewSet):
    queryset = Activity.objects.select_related("status", "property").prefetch_related(
        "species"
    )
    serializer_class = ActivitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(property_id=property_id)
        return filter_is_public(qs, self.request)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(), created_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


def _get_activity_in_scope(request, activity_id):
    """Org-scoped lookup for the plain function-based photo views below,
    which aren't ModelViewSets and so don't get OrganizationScopedViewSet's
    filtering for free."""
    membership = get_active_membership(request.user)
    organization = membership.organization if membership else None
    return get_object_or_404(Activity, id=activity_id, organization=organization)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def activity_photos(request, activity_id):
    """List an activity's photos, or upload a new one (multipart form,
    field name `image`) — see ActivityPhoto's DB-storage decision in
    models.py."""
    activity = _get_activity_in_scope(request, activity_id)

    if request.method == "POST":
        ensure_role(request.user, Membership.Role.EDITOR)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "No image file provided."}, status=400)
        if not (image.content_type or "").startswith("image/"):
            return Response({"detail": "Only image uploads are supported."}, status=400)
        if image.size > MAX_PHOTO_BYTES:
            return Response({"detail": "Image is too large (max 8MB)."}, status=400)
        photo = ActivityPhoto.objects.create(
            activity=activity, image=image.read(), content_type=image.content_type
        )
        serializer = ActivityPhotoSerializer(photo, context={"request": request})
        return Response(serializer.data, status=201)

    photos = activity.photos.all()
    serializer = ActivityPhotoSerializer(photos, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def activity_photo_detail(request, activity_id, photo_id):
    activity = _get_activity_in_scope(request, activity_id)
    ensure_role(request.user, Membership.Role.ADMIN)
    photo = get_object_or_404(ActivityPhoto, id=photo_id, activity=activity)
    photo.delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def activity_photo_image(request, activity_id, photo_id):
    """Raw image bytes for use as an <img src>. Session cookies ride along
    on same-site image requests, so this is auth-checked the same as any
    other endpoint — see frontend/src/api/client.ts for the corresponding
    same-site assumption on the frontend dev server's origin."""
    activity = _get_activity_in_scope(request, activity_id)
    photo = get_object_or_404(ActivityPhoto, id=photo_id, activity=activity)
    return HttpResponse(bytes(photo.image), content_type=photo.content_type)
