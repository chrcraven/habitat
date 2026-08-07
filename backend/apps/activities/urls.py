from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("activities", views.ActivityViewSet, basename="activity")
router.register("workflow-states", views.WorkflowStateViewSet, basename="workflow-state")

urlpatterns = [
    path("activities/<int:activity_id>/photos/", views.activity_photos, name="activity-photos"),
    path(
        "activities/<int:activity_id>/photos/<int:photo_id>/",
        views.activity_photo_detail,
        name="activity-photo-detail",
    ),
    path(
        "activities/<int:activity_id>/photos/<int:photo_id>/image/",
        views.activity_photo_image,
        name="activity-photo-image",
    ),
] + router.urls
