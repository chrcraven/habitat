from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("sightings", views.SightingViewSet, basename="sighting")

urlpatterns = router.urls
