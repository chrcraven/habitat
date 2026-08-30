from django.urls import path

from . import views

urlpatterns = [
    path("organizations/<int:org_id>/", views.organization_detail, name="public-organization"),
    path("properties/<int:property_id>/", views.property_detail, name="public-property"),
    # Vanity-slug entry points (see /docs/open-questions.md, "Vanity slug
    # URLs"). `o/` prefix keeps them clearly separate from the numeric
    # `organizations/` / `properties/` routes above.
    path("o/<slug:org_slug>/", views.organization_detail_by_slug, name="public-organization-slug"),
    path(
        "o/<slug:org_slug>/<slug:property_slug>/",
        views.property_detail_by_slug,
        name="public-property-slug",
    ),
    path(
        "properties/<int:property_id>/activities/",
        views.property_activities,
        name="public-property-activities",
    ),
    path(
        "properties/<int:property_id>/sightings/",
        views.property_sightings,
        name="public-property-sightings",
    ),
    # Authored pages (see /docs/open-questions.md, "Public site
    # storytelling / custom content") — slug-only, no numeric-ID
    # equivalent (this is a brand-new resource, no back-compat URL to
    # preserve). Deliberately namespaced under the same `o/<org-slug>/...`
    # prefix as the slug-based org/property views above, not the numeric
    # `organizations/`/`properties/` ones.
    path(
        "o/<slug:org_slug>/pages/<slug:page_slug>/",
        views.organization_page_detail,
        name="public-organization-page",
    ),
    path(
        "o/<slug:org_slug>/<slug:property_slug>/pages/<slug:page_slug>/",
        views.property_page_detail,
        name="public-property-page",
    ),
    path("activities/<int:activity_id>/photos/", views.activity_photos, name="public-activity-photos"),
    path(
        "activities/<int:activity_id>/photos/<int:photo_id>/image/",
        views.activity_photo_image,
        name="public-activity-photo-image",
    ),
    path("sightings/<int:sighting_id>/photos/", views.sighting_photos, name="public-sighting-photos"),
    path(
        "sightings/<int:sighting_id>/photos/<int:photo_id>/image/",
        views.sighting_photo_image,
        name="public-sighting-photo-image",
    ),
]
