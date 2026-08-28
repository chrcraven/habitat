"""
Unauthenticated read-only API for Habitat's public site (Phase 2 —
see /docs/roadmap.md and /CLAUDE.md's task log). Two "shapes" of public
page, per the request that started this: **per-property** (one property's
public activities/sightings) and **per-organization** (a portfolio of that
org's public properties) — this module backs both, plus the photo endpoints
either one needs.

Nothing here requires a session — REST_FRAMEWORK's global
IsAuthenticated default (see config/settings.py) is overridden to AllowAny
on every view below, deliberately, since the whole point is that a visitor
with no account can load these. What keeps this from exposing everything
in an org's account is consistent filtering: every query here is scoped to
`is_public=True` (Property, Activity, Sighting each have their own
independent flag — see /docs/data-model-notes.md and the Property model
docstring) and a 404 rather than a 403 on anything private, so a guessed
ID for a private record doesn't even confirm it exists.

No slugs/vanity URLs yet — public URLs are just numeric IDs
(`/public/org/<id>`, `/public/properties/<id>` on the frontend). Fine for
Phase 1/2; a slug would be a nicer public-facing URL later (see
/docs/open-questions.md).
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Organization, Property
from apps.accounts.serializers import OrganizationSerializer, PropertySerializer
from apps.activities.models import Activity, ActivityPhoto
from apps.activities.serializers import ActivitySerializer
from apps.sightings.models import Sighting, SightingActivityLink, SightingPhoto
from apps.sightings.serializers import SightingSerializer

from .serializers import PublicActivityPhotoSerializer, PublicSightingPhotoSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def organization_detail(request, org_id):
    """The org-level "portfolio" page: org name + every public property it
    has. A property with is_public=False (or any property belonging to an
    org with none public) simply doesn't appear — no "N hidden" count or
    other hint of what's not shown."""
    organization = get_object_or_404(Organization, id=org_id)
    properties = Property.objects.filter(organization=organization, is_public=True).order_by(
        "name"
    )
    return Response(
        {
            "organization": OrganizationSerializer(organization).data,
            "properties": PropertySerializer(
                properties, many=True, context={"request": request}
            ).data,
        }
    )


def _public_property_or_404(property_id):
    return get_object_or_404(Property, id=property_id, is_public=True)


def _public_linked_sighting_ids(activity_ids):
    """activity id -> list of linked sighting ids, filtered to links where
    the sighting side is also public (and on a public property) — so a
    public visitor can never infer the existence of a private sighting via
    an activity's link list. See property_activities below."""
    links = SightingActivityLink.objects.filter(
        activity_id__in=activity_ids,
        sighting__is_public=True,
        sighting__property__is_public=True,
    ).values_list("activity_id", "sighting_id")
    result: dict[int, list[int]] = {}
    for activity_id, sighting_id in links:
        result.setdefault(activity_id, []).append(sighting_id)
    return result


def _public_linked_activity_ids(sighting_ids):
    """Mirror of _public_linked_sighting_ids, for a sighting's linked
    activities — see property_sightings below."""
    links = SightingActivityLink.objects.filter(
        sighting_id__in=sighting_ids,
        activity__is_public=True,
        activity__property__is_public=True,
    ).values_list("sighting_id", "activity_id")
    result: dict[int, list[int]] = {}
    for sighting_id, activity_id in links:
        result.setdefault(sighting_id, []).append(activity_id)
    return result


@api_view(["GET"])
@permission_classes([AllowAny])
def property_detail(request, property_id):
    property_ = _public_property_or_404(property_id)
    data = PropertySerializer(property_, context={"request": request}).data
    data["organization"] = OrganizationSerializer(property_.organization).data
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def property_activities(request, property_id):
    """Surfaces each activity's linked (public) sightings alongside the
    usual fields — e.g. "reported by a visitor, treated on this date" (see
    /docs/open-questions.md, "Public-facing behavior") — the direct
    Sighting↔Activity link (data-model-notes.md) is otherwise only visible
    to logged-in users via LinkedRecordsPanel."""
    property_ = _public_property_or_404(property_id)
    activities = Activity.objects.filter(property=property_, is_public=True).select_related(
        "status"
    )
    data = ActivitySerializer(activities, many=True, context={"request": request}).data
    linked = _public_linked_sighting_ids([f["id"] for f in data["features"]])
    for feature in data["features"]:
        feature["properties"]["linked_sighting_ids"] = linked.get(feature["id"], [])
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def property_sightings(request, property_id):
    """Mirror of property_activities above, for each sighting's linked
    (public) activities."""
    property_ = _public_property_or_404(property_id)
    sightings = Sighting.objects.filter(property=property_, is_public=True).select_related(
        "species"
    )
    data = SightingSerializer(sightings, many=True, context={"request": request}).data
    linked = _public_linked_activity_ids([f["id"] for f in data["features"]])
    for feature in data["features"]:
        feature["properties"]["linked_activity_ids"] = linked.get(feature["id"], [])
    return Response(data)


def _public_activity_or_404(activity_id):
    """Also requires the activity's *property* to still be public — a
    property flipped private after one of its activities was created
    shouldn't leave that activity's photos reachable by a stale/guessed
    URL."""
    return get_object_or_404(
        Activity, id=activity_id, is_public=True, property__is_public=True
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def activity_photos(request, activity_id):
    activity = _public_activity_or_404(activity_id)
    photos = activity.photos.all()
    return Response(
        PublicActivityPhotoSerializer(photos, many=True, context={"request": request}).data
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def activity_photo_image(request, activity_id, photo_id):
    activity = _public_activity_or_404(activity_id)
    photo = get_object_or_404(ActivityPhoto, id=photo_id, activity=activity)
    return HttpResponse(bytes(photo.image), content_type=photo.content_type)


def _public_sighting_or_404(sighting_id):
    return get_object_or_404(
        Sighting, id=sighting_id, is_public=True, property__is_public=True
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def sighting_photos(request, sighting_id):
    sighting = _public_sighting_or_404(sighting_id)
    photos = sighting.photos.all()
    return Response(
        PublicSightingPhotoSerializer(photos, many=True, context={"request": request}).data
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def sighting_photo_image(request, sighting_id, photo_id):
    sighting = _public_sighting_or_404(sighting_id)
    photo = get_object_or_404(SightingPhoto, id=photo_id, sighting=sighting)
    return HttpResponse(bytes(photo.image), content_type=photo.content_type)
