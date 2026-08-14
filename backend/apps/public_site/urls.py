from django.urls import path

from . import views

urlpatterns = [
    path("organizations/<int:org_id>/", views.organization_detail, name="public-organization"),
    path("properties/<int:property_id>/", views.property_detail, name="public-property"),
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
