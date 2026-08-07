from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("activities", views.ActivityViewSet, basename="activity")
router.register("workflow-states", views.WorkflowStateViewSet, basename="workflow-state")

urlpatterns = router.urls
