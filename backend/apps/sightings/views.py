from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Membership
from apps.accounts.org_scoping import (
    OrganizationScopedViewSet,
    ensure_property_accessible,
    ensure_role,
    filter_by_property_scope,
    filter_is_public,
    get_active_membership,
    scoped_property_ids,
)
from apps.activities.models import Activity

from .models import Sighting, SightingActivityLink, SightingPhoto
from .serializers import SightingActivityLinkSerializer, SightingPhotoSerializer, SightingSerializer

MAX_PHOTO_BYTES = 8 * 1024 * 1024

# A soft-deleted property's sightings hide too (see ActivityViewSet's
# matching comment in apps/activities/views.py) — but Sighting.property is
# optional (SET_NULL, a sighting may not fall within any drawn boundary at
# all), so unlike Activity this needs an OR: keep a sighting if it either
# has no property, or its property isn't (yet) soft-deleted.
_NOT_DELETED = Q(property__isnull=True) | Q(property__deleted_at__isnull=True)


class SightingViewSet(OrganizationScopedViewSet):
    queryset = Sighting.objects.select_related("species", "property")
    serializer_class = SightingSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(_NOT_DELETED)
        # Property-scoped roles (see /docs/open-questions.md,
        # "Property-scoped role enforcement") — a scoped membership only
        # sees sightings tied to one of its own properties; a
        # no-property sighting (property is optional here) has nothing to
        # scope it to, so it's invisible to a scoped membership even
        # though an account-wide one still sees it.
        qs = filter_by_property_scope(qs, get_active_membership(self.request.user))
        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(property_id=property_id)
        return filter_is_public(qs, self.request)

    def perform_create(self, serializer):
        # A brand-new sighting starts from its property's own
        # sightings_public_by_default (see Property model docstring) unless
        # the request explicitly set is_public itself — the frontend's
        # create form is expected to seed its checkbox from that same
        # default (see SightingFormPage), so in practice this only matters
        # for a caller that omits the field outright (e.g. a future public
        # API client).
        extra = {}
        if "is_public" not in self.request.data:
            property_obj = serializer.validated_data.get("property")
            if property_obj is not None:
                extra["is_public"] = property_obj.sightings_public_by_default
        serializer.save(
            organization=self.get_organization(), created_by=self.request.user, **extra
        )


def _get_sighting_in_scope(request, sighting_id):
    membership = get_active_membership(request.user)
    organization = membership.organization if membership else None
    qs = Sighting.objects.filter(_NOT_DELETED, organization=organization)
    ids = scoped_property_ids(membership)
    if ids is not None:
        qs = qs.filter(property_id__in=ids)
    return get_object_or_404(qs, id=sighting_id)


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
        # `sighting` is already scope-checked (see _get_sighting_in_scope);
        # also check the *activity* side (its property is required, so the
        # plain — not "optional" — variant), so a property-scoped member
        # can't use the link endpoint to reference an activity outside
        # their own scope.
        ensure_property_accessible(get_active_membership(request.user), activity.property)
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
