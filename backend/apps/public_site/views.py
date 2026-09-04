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

**Two conditions, not one.** A record is public here only if it is flagged
public *and* its property has not been soft-deleted. Those are separate
checks and the second one is easy to lose: `Property.objects` filters out
soft-deleted rows, but a *related-field* filter (`property__is_public`) is
a plain SQL join that never consults that manager, and a soft-deleted
property keeps `is_public=True`. Any new query in this module that reaches
a Property through a join must therefore carry
`…property__deleted_at__isnull=True` explicitly — see
`_public_activity_or_404`. Getting this wrong is not hypothetical: between
2026-08-29 (when soft delete shipped, covering the authenticated app but
never this module) and 2026-09-04, deleting a property left its already-
published photos serving here, so the *stronger* action retracted *less*
than flipping the property private did.

Public pages are reachable two ways: the original numeric-ID URLs
(`/public/organizations/<id>/`, `/public/properties/<id>/`) — kept working
for backward compatibility — and the newer vanity-slug URLs
(`/public/o/<org-slug>/`, `/public/o/<org-slug>/<property-slug>/`, decided
2026-08-28, see /docs/open-questions.md, "Vanity slug URLs"). Both resolve
to the same response bodies via the `_organization_payload` /
`_property_payload` helpers below; the slug views just look the row up by
slug (still gated on is_public / 404-not-403, same as the numeric ones)
before delegating. The activity/sighting/photo sub-resources stay numeric —
once a property is resolved by slug, its numeric id drives those.
"""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Organization, Property
from apps.accounts.serializers import OrganizationSerializer, PropertySerializer
from apps.activities.models import Activity, ActivityPhoto
from apps.activities.serializers import ActivitySerializer
from apps.pages.custom_html import organization_allows_custom_html
from apps.pages.models import Page
from apps.sightings.models import Sighting, SightingActivityLink, SightingPhoto
from apps.sightings.serializers import SightingSerializer

from .page_serializers import PublicPageDetailSerializer, PublicPageListSerializer
from .serializers import PublicActivityPhotoSerializer, PublicSightingPhotoSerializer


def _public_pages(*, organization=None, property=None):
    """Public (is_public=True) pages for one scope — either an org's own
    org-level pages (property=None) or one property's own pages. Shared by
    the org/property payload helpers (nav list) and the page-detail views
    below (existence + visibility check)."""
    if property is not None:
        return Page.objects.public().filter(property=property)
    return Page.objects.public().filter(organization=organization, property__isnull=True)


def _landing_page_slug(landing_page):
    """None means the built-in Explore view; otherwise the authored page's
    slug — but only if that page is still actually public (an admin could
    have picked a page as the landing page and then unpublished it, in
    which case falling back to Explore is safer than 404ing the org/
    property's own root URL)."""
    if landing_page is None or not landing_page.is_public:
        return None
    return landing_page.slug


def _organization_payload(request, organization):
    """The org-level "portfolio" page body: org name + every public
    property it has, plus the org's public authored pages (for the page
    nav — see /docs/open-questions.md, "Public site storytelling") and
    which one (if any) is the landing page. A property with
    is_public=False (or any property belonging to an org with none public)
    simply doesn't appear — no "N hidden" count or other hint of what's
    not shown. Shared by the numeric-ID and slug views."""
    properties = Property.objects.filter(organization=organization, is_public=True).order_by(
        "name"
    )
    pages = _public_pages(organization=organization).order_by("position", "id")
    return {
        "organization": OrganizationSerializer(organization).data,
        "properties": PropertySerializer(
            properties, many=True, context={"request": request}
        ).data,
        "pages": PublicPageListSerializer(pages, many=True).data,
        "landing_page_slug": _landing_page_slug(organization.landing_page),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def organization_detail(request, org_id):
    organization = get_object_or_404(Organization, id=org_id)
    return Response(_organization_payload(request, organization))


@api_view(["GET"])
@permission_classes([AllowAny])
def organization_detail_by_slug(request, org_slug):
    """Vanity-slug equivalent of organization_detail — `/public/o/<slug>/`."""
    organization = get_object_or_404(Organization, slug=org_slug)
    return Response(_organization_payload(request, organization))


def _public_property_or_404(property_id):
    return get_object_or_404(Property, id=property_id, is_public=True)


def _public_linked_sighting_ids(activity_ids):
    """activity id -> list of linked sighting ids, filtered to links where
    the sighting side is also public (and on a public, not-deleted
    property) — so a public visitor can never infer the existence of a
    private sighting via an activity's link list. See property_activities
    below.

    The `deleted_at` clause matters here even though the *activity* side is
    always on a live property (property_activities resolved it through
    `_public_property_or_404`): a link is not constrained to a single
    property — nothing in SightingActivityLinkSerializer enforces that, and
    it even serves `activity_property_name` — so the sighting on the other
    end may sit on a *different*, since-deleted property. Same join
    semantics as `_public_activity_or_404`; see that helper.
    """
    links = SightingActivityLink.objects.filter(
        activity_id__in=activity_ids,
        sighting__is_public=True,
        sighting__property__is_public=True,
        sighting__property__deleted_at__isnull=True,
    ).values_list("activity_id", "sighting_id")
    result: dict[int, list[int]] = {}
    for activity_id, sighting_id in links:
        result.setdefault(activity_id, []).append(sighting_id)
    return result


def _public_linked_activity_ids(sighting_ids):
    """Mirror of _public_linked_sighting_ids, for a sighting's linked
    activities — see property_sightings below, and that helper for why the
    cross-property `deleted_at` clause is needed."""
    links = SightingActivityLink.objects.filter(
        sighting_id__in=sighting_ids,
        activity__is_public=True,
        activity__property__is_public=True,
        activity__property__deleted_at__isnull=True,
    ).values_list("sighting_id", "activity_id")
    result: dict[int, list[int]] = {}
    for sighting_id, activity_id in links:
        result.setdefault(sighting_id, []).append(activity_id)
    return result


def _property_payload(request, property_):
    data = PropertySerializer(property_, context={"request": request}).data
    data["organization"] = OrganizationSerializer(property_.organization).data
    pages = _public_pages(property=property_).order_by("position", "id")
    data["pages"] = PublicPageListSerializer(pages, many=True).data
    data["landing_page_slug"] = _landing_page_slug(property_.landing_page)
    return data


@api_view(["GET"])
@permission_classes([AllowAny])
def property_detail(request, property_id):
    property_ = _public_property_or_404(property_id)
    return Response(_property_payload(request, property_))


@api_view(["GET"])
@permission_classes([AllowAny])
def property_detail_by_slug(request, org_slug, property_slug):
    """Vanity-slug equivalent of property_detail —
    `/public/o/<org-slug>/<property-slug>/`. Both the property and its org
    are matched by slug; still gated on is_public with a 404 (not 403) so a
    guessed slug on a private property reveals nothing."""
    property_ = get_object_or_404(
        Property,
        slug=property_slug,
        organization__slug=org_slug,
        is_public=True,
    )
    return Response(_property_payload(request, property_))


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


def _page_document(page):
    """Serve one custom-HTML page's author document verbatim — scripts and
    all — as its own top-level document, which is the entire mechanism that
    makes the owner's 2026-09-02 "arbitrary author HTML/JS" decision safe
    to honour (see /docs/open-questions.md, "Public site storytelling /
    custom content", and apps/pages/models.py's docstring).

    Three response headers do the work, and they matter in this order:

    * `Content-Security-Policy: sandbox allow-scripts` — the load-bearing
      one. It applies the iframe sandbox to the *document itself*, so the
      browser assigns it a unique opaque origin whether it's framed by the
      public site or opened directly in a tab. Author script therefore
      can't read Habitat's cookies or storage, can't make same-origin
      requests, and can't reach the embedding page's DOM. Crucially
      `allow-same-origin` is NOT granted: with it, a sandboxed document can
      simply remove its own sandbox. This holds even when the public site
      is served from the app's own origin, which is why the feature isn't
      gated on PUBLIC_SITE_URL being set — relocating the public site is
      defence in depth on top of this, not the thing that provides it.
    * `frame-ancestors` — only Habitat's own origins may embed it, so the
      document can't be framed into someone else's site to lend it
      Habitat's context. That's `'self'` plus the two origins a Habitat
      frontend is actually served from when it isn't the API's own:
      FRONTEND_URL (the app, which in local dev is Vite on another port)
      and PUBLIC_SITE_URL (the isolated public origin, once a deployment
      relocates the public site there). Omitting either would leave the
      frame silently blank in exactly the deployments this feature is for.
    * `X-Content-Type-Options: nosniff` — pin it to text/html; never let a
      browser re-interpret an author document as something else.

    Django's XFrameOptionsMiddleware would otherwise stamp `DENY` here and
    break the embed, hence @xframe_options_exempt on the callers —
    `frame-ancestors` above is the modern, more precise replacement it
    defers to.

    404s (rather than serving it) when the page's organization has had
    custom content switched off, so the per-tenant kill-switch actually
    takes effect on already-published pages, not just on new edits.
    """
    if not page.is_custom_html() or not organization_allows_custom_html(page.organization):
        raise Http404("No custom-HTML document for this page.")
    response = HttpResponse(page.body, content_type="text/html; charset=utf-8")
    ancestors = " ".join(
        dict.fromkeys(
            [
                "'self'",
                *[
                    origin
                    for origin in (settings.FRONTEND_URL, settings.PUBLIC_SITE_URL)
                    if origin
                ],
            ]
        )
    )
    response["Content-Security-Policy"] = f"sandbox allow-scripts; frame-ancestors {ancestors}"
    response["X-Content-Type-Options"] = "nosniff"
    # An author document is per-page content that changes when they edit
    # it; let a browser cache it briefly but always revalidate, so an edit
    # shows up without a hard refresh.
    response["Cache-Control"] = "no-cache"
    return response


@api_view(["GET"])
@permission_classes([AllowAny])
def organization_page_detail(request, org_slug, page_slug):
    """One of an org's own authored pages —
    `/public/o/<org-slug>/pages/<page-slug>/`. 404s (not just an empty
    body) for a private or nonexistent page/org, same "don't confirm what's
    behind a guessed slug" posture as everywhere else in this app. The
    reserved "explore" slug never matches a stored Page (see
    apps/pages/models.py's RESERVED_PAGE_SLUGS) — the frontend renders the
    built-in Explore view for that slug entirely client-side, from the
    same organization_detail(_by_slug) payload it already has.
    """
    organization = get_object_or_404(Organization, slug=org_slug)
    page = get_object_or_404(
        Page, organization=organization, property__isnull=True, slug=page_slug, is_public=True
    )
    return Response(PublicPageDetailSerializer(page, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
@xframe_options_exempt
def organization_page_document(request, org_slug, page_slug):
    """The raw author document for a custom-HTML org-level page —
    `/public/o/<org-slug>/pages/<page-slug>/document/`. See
    `_page_document` for what makes serving this verbatim safe."""
    organization = get_object_or_404(Organization, slug=org_slug)
    page = get_object_or_404(
        Page, organization=organization, property__isnull=True, slug=page_slug, is_public=True
    )
    return _page_document(page)


@api_view(["GET"])
@permission_classes([AllowAny])
def property_page_detail(request, org_slug, property_slug, page_slug):
    """Mirror of organization_page_detail above, for one property's own
    authored pages — `/public/o/<org-slug>/<property-slug>/pages/<page-slug>/`."""
    property_ = get_object_or_404(
        Property, slug=property_slug, organization__slug=org_slug, is_public=True
    )
    page = get_object_or_404(Page, property=property_, slug=page_slug, is_public=True)
    return Response(PublicPageDetailSerializer(page, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
@xframe_options_exempt
def property_page_document(request, org_slug, property_slug, page_slug):
    """Mirror of organization_page_document, for a property's own
    custom-HTML page."""
    property_ = get_object_or_404(
        Property, slug=property_slug, organization__slug=org_slug, is_public=True
    )
    page = get_object_or_404(Page, property=property_, slug=page_slug, is_public=True)
    return _page_document(page)


def _public_activity_or_404(activity_id):
    """Also requires the activity's *property* to still be public **and not
    soft-deleted** — a property flipped private, or deleted, after one of
    its activities was created shouldn't leave that activity's photos
    reachable by a stale/guessed URL.

    The `deleted_at` half is not redundant with `is_public`, and the reason
    is the one Django semantic this whole module has to get right: a
    related-field filter like `property__is_public=True` compiles to a
    plain SQL join and does **not** consult the related model's default
    manager, so `Property.objects`' soft-delete filter (see
    apps/accounts/models.py's PropertyManager) has no effect here. A
    soft-deleted property still has `is_public=True` — only `deleted_at`
    changed — so without this line the join keeps matching and the photos
    keep serving. Contrast `_public_property_or_404` above, which passes a
    model *class* to get_object_or_404 and therefore does go through the
    filtering default manager.
    """
    return get_object_or_404(
        Activity,
        id=activity_id,
        is_public=True,
        property__is_public=True,
        property__deleted_at__isnull=True,
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


@api_view(["GET"])
@permission_classes([AllowAny])
def organization_theme_image(request, org_id):
    """An org's header banner image, for the "constrained theme controls"
    feature (see apps/accounts/theming.py). Numeric only, same convention
    as every other sub-resource in this module (activity/sighting photos
    stay numeric even when the page itself is reached by slug) — the
    frontend already has the numeric id from the org/property payload it
    already fetched. Organization has no is_public gate of its own (only
    Property does — see that model's docstring), so this is always
    reachable once an org has a header image set, same as the rest of the
    org-portfolio payload."""
    organization = get_object_or_404(Organization, id=org_id)
    if not organization.theme_header_image_content_type:
        return HttpResponse(status=404)
    return HttpResponse(
        bytes(organization.theme_header_image),
        content_type=organization.theme_header_image_content_type,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def property_theme_image(request, property_id):
    """Mirror of organization_theme_image above, for one property's own
    header image — gated on is_public like every other property
    sub-resource here."""
    property_ = _public_property_or_404(property_id)
    if not property_.theme_header_image_content_type:
        return HttpResponse(status=404)
    return HttpResponse(
        bytes(property_.theme_header_image),
        content_type=property_.theme_header_image_content_type,
    )


def _public_sighting_or_404(sighting_id):
    """Mirror of _public_activity_or_404 — see that helper for why the
    `deleted_at` filter is load-bearing rather than redundant.

    Unlike the authenticated side (apps/sightings/views.py's `_NOT_DELETED`,
    which has to OR in `property__isnull=True` because Sighting.property is
    optional), no OR is needed here: `property__is_public=True` already
    requires a property, so a property-less sighting was never reachable
    publicly in the first place.
    """
    return get_object_or_404(
        Sighting,
        id=sighting_id,
        is_public=True,
        property__is_public=True,
        property__deleted_at__isnull=True,
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
