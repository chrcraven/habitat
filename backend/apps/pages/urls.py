from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("pages", views.PageViewSet, basename="page")

urlpatterns = router.urls
