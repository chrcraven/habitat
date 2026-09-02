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
    ensure_optional_property_accessible,
    ensure_role,
    filter_by_property_scope,
    filter_is_public,
    get_active_membership,
    scoped_property_ids,
)

from apps.sightings.models import Sighting, SightingActivityLink
from apps.sightings.serializers import SightingActivityLinkSerializer
from apps.species.models import Species

from .models import Activity, ActivityPhoto, ActivitySpecies, ActivityType, WorkflowState
from .serializers import (
    ActivityPhotoSerializer,
    ActivitySerializer,
    ActivitySpeciesSerializer,
    ActivityTypeSerializer,
    WorkflowStateSerializer,
)

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


class ActivityTypeViewSet(OrganizationScopedViewSet):
    """An org's own activity types (owner decision, 2026-09-02 — see
    models.py#ActivityType). Unlike WorkflowStateViewSet above, this one
    is writable: "editable" is the whole point of the change. Roles follow
    the same convention as everywhere else via OrganizationScopedViewSet —
    any member reads, editor+ creates/updates, admin deletes."""

    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # The uniqueness check in ActivityTypeSerializer.validate_name
        # needs the org, which never comes from the request body.
        context["organization"] = self.get_organization()
        return context

    def destroy(self, request, *args, **kwargs):
        # Activity.activity_type is PROTECT, so deleting a type that's in
        # use raises ProtectedError — which would surface as a 500. Say
        # what actually happened instead, and how many records are in the
        # way, so an admin can go and retype them.
        instance = self.get_object()
        in_use = instance.activities.count()
        if in_use:
            return Response(
                {
                    "detail": (
                        f"{in_use} activit{'y still uses' if in_use == 1 else 'ies still use'} "
                        "this type. "
                        "Change them to another type first."
                    )
                },
                status=400,
            )
        return super().destroy(request, *args, **kwargs)


class ActivityViewSet(OrganizationScopedViewSet):
    queryset = Activity.objects.select_related(
        "status", "property", "activity_type"
    ).prefetch_related("species")
    serializer_class = ActivitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Hide activities belonging to a soft-deleted property (see
        # apps/accounts/models.py's Property.deleted_at) — Activity itself
        # isn't soft-deleted, only its property is, but the decided
        # cascade behavior is that a deleted property's records disappear
        # from the app too during the 30-day restore window. Activity's
        # `property` FK is required (CASCADE, not nullable), so a plain
        # join filter is enough — contrast Sighting below, whose property
        # is optional.
        qs = qs.filter(property__deleted_at__isnull=True)
        # Property-scoped roles (see /docs/open-questions.md,
        # "Property-scoped role enforcement") — a scoped membership only
        # ever sees activities on its own properties.
        qs = filter_by_property_scope(qs, get_active_membership(self.request.user))
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
    """Org- and property-scoped lookup for the plain function-based photo/
    links/species views below, which aren't ModelViewSets and so don't get
    OrganizationScopedViewSet's (or ActivityViewSet's own property-scope)
    filtering for free."""
    membership = get_active_membership(request.user)
    organization = membership.organization if membership else None
    qs = Activity.objects.filter(
        organization=organization, property__deleted_at__isnull=True
    )
    ids = scoped_property_ids(membership)
    if ids is not None:
        qs = qs.filter(property_id__in=ids)
    return get_object_or_404(qs, id=activity_id)


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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def activity_links(request, activity_id):
    """The activity side of the direct Sighting↔Activity link — mirrors
    apps/sightings/views.py's sighting_links (same model, same
    serializer), so a link can be created or browsed from whichever
    record's edit page the user happens to be on."""
    activity = _get_activity_in_scope(request, activity_id)

    if request.method == "POST":
        ensure_role(request.user, Membership.Role.EDITOR)
        sighting = get_object_or_404(
            Sighting, id=request.data.get("sighting"), organization=activity.organization
        )
        # `activity` is already scope-checked (see _get_activity_in_scope);
        # also check the *sighting* side, so a property-scoped member can't
        # use the link endpoint to reference a sighting outside their own
        # scope. Sighting.property is optional, so this is the "optional"
        # variant — an account-wide member can still link to a
        # property-less sighting, same as before this change.
        ensure_optional_property_accessible(get_active_membership(request.user), sighting.property)
        link, created = SightingActivityLink.objects.get_or_create(
            sighting=sighting, activity=activity, defaults={"linked_by": request.user}
        )
        if not created:
            return Response({"detail": "Already linked to that sighting."}, status=400)
        return Response(SightingActivityLinkSerializer(link).data, status=201)

    links = SightingActivityLink.objects.filter(activity=activity).select_related(
        "sighting", "sighting__species", "activity__property"
    )
    return Response(SightingActivityLinkSerializer(links, many=True).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def activity_link_detail(request, activity_id, link_id):
    activity = _get_activity_in_scope(request, activity_id)
    ensure_role(request.user, Membership.Role.EDITOR)
    link = get_object_or_404(SightingActivityLink, id=link_id, activity=activity)
    link.delete()
    return Response(status=204)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def activity_species_list(request, activity_id):
    """Species linked to this activity via the ActivitySpecies through
    model (role/quantity/detail per species) — see that model's
    docstring and ActivitySpeciesSerializer. A separate surface from
    ActivitySerializer's read-only `species_names` for the reason given
    in that serializer's docstring: Django M2M .set() doesn't work
    against a custom `through` model."""
    activity = _get_activity_in_scope(request, activity_id)

    if request.method == "POST":
        ensure_role(request.user, Membership.Role.EDITOR)
        species = get_object_or_404(
            Species, id=request.data.get("species"), organization=activity.organization
        )
        link, created = ActivitySpecies.objects.get_or_create(
            activity=activity,
            species=species,
            defaults={
                "role": request.data.get("role", ""),
                "quantity": request.data.get("quantity") or None,
                "detail": request.data.get("detail", ""),
            },
        )
        if not created:
            return Response({"detail": "That species is already linked to this activity."}, status=400)
        return Response(ActivitySpeciesSerializer(link).data, status=201)

    links = ActivitySpecies.objects.filter(activity=activity).select_related("species")
    return Response(ActivitySpeciesSerializer(links, many=True).data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def activity_species_detail(request, activity_id, link_id):
    activity = _get_activity_in_scope(request, activity_id)
    ensure_role(request.user, Membership.Role.EDITOR)
    link = get_object_or_404(ActivitySpecies, id=link_id, activity=activity)

    if request.method == "DELETE":
        link.delete()
        return Response(status=204)

    serializer = ActivitySpeciesSerializer(link, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
