from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("sightings", views.SightingViewSet, basename="sighting")

urlpatterns = [
    path("sightings/<int:sighting_id>/photos/", views.sighting_photos, name="sighting-photos"),
    path(
        "sightings/<int:sighting_id>/photos/<int:photo_id>/",
        views.sighting_photo_detail,
        name="sighting-photo-detail",
    ),
    path(
        "sightings/<int:sighting_id>/photos/<int:photo_id>/image/",
        views.sighting_photo_image,
        name="sighting-photo-image",
    ),
] + router.urls
