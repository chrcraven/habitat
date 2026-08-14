from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Membership
from apps.accounts.org_scoping import (
    OrganizationScopedViewSet,
    ensure_role,
    filter_is_public,
    get_active_membership,
)
from apps.activities.models import Activity

from .models import Sighting, SightingActivityLink, SightingPhoto
from .serializers import SightingActivityLinkSerializer, SightingPhotoSerializer, SightingSerializer

MAX_PHOTO_BYTES = 8 * 1024 * 1024


class SightingViewSet(OrganizationScopedViewSet):
    queryset = Sighting.objects.select_related("species", "property")
    serializer_class = SightingSerializer

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


def _get_sighting_in_scope(request, sighting_id):
    membership = get_active_membership(request.user)
    organization = membership.organization if membership else None
    return get_object_or_404(Sighting, id=sighting_id, organization=organization)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def sighting_photos(request, sighting_id):
    sighting = _get_sighting_in_scope(request, sighting_id)

    if request.method == "POST":
        ensure_role(request.user, Membership.Role.EDITOR)
        image = request.FILES.get("image")
        if not image:
            return Response({"detail": "No image file provided."}, status=400)
        if not (image.content_type or "").startswith("image/"):
            return Response({"detail": "Only image uploads are supported."}, status=400)
        if image.size > MAX_PHOTO_BYTES:
            return Response({"detail": "Image is too large (max 8MB)."}, status=400)
        photo = SightingPhoto.objects.create(
            sighting=sighting, image=image.read(), content_type=image.content_type
        )
        serializer = SightingPhotoSerializer(photo, context={"request": request})
        return Response(serializer.data, status=201)

    photos = sighting.photos.all()
    serializer = SightingPhotoSerializer(photos, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def sighting_photo_detail(request, sighting_id, photo_id):
    sighting = _get_sighting_in_scope(request, sighting_id)
    ensure_role(request.user, Membership.Role.ADMIN)
    photo = get_object_or_404(SightingPhoto, id=photo_id, sighting=sighting)
    photo.delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sighting_photo_image(request, sighting_id, photo_id):
    sighting = _get_sighting_in_scope(request, sighting_id)
    photo = get_object_or_404(SightingPhoto, id=photo_id, sighting=sighting)
    return HttpResponse(bytes(photo.image), content_type=photo.content_type)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def sighting_links(request, sighting_id):
    """List or create direct Sighting↔Activity links (see
    SightingActivityLink in models.py) — created directly, not gated
    behind a Task, per the decided data model. The activity side of this
    same relationship is apps/activities/views.py's activity_links."""
    sighting = _get_sighting_in_scope(request, sighting_id)

    if request.method == "POST":
        ensure_role(request.user, Membership.Role.EDITOR)
        activity = get_object_or_404(
            Activity, id=request.data.get("activity"), organization=sighting.organization
        )
        link, created = SightingActivityLink.objects.get_or_create(
            sighting=sighting, activity=activity, defaults={"linked_by": request.user}
        )
        if not created:
            return Response({"detail": "Already linked to that activity."}, status=400)
        return Response(SightingActivityLinkSerializer(link).data, status=201)

    links = SightingActivityLink.objects.filter(sighting=sighting).select_related(
        "activity", "activity__property", "sighting__species"
    )
    return Response(SightingActivityLinkSerializer(links, many=True).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def sighting_link_detail(request, sighting_id, link_id):
    sighting = _get_sighting_in_scope(request, sighting_id)
    ensure_role(request.user, Membership.Role.EDITOR)
    link = get_object_or_404(SightingActivityLink, id=link_id, sighting=sighting)
    link.delete()
    return Response(status=204)
