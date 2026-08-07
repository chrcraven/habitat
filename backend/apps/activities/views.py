from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.accounts.org_scoping import OrganizationScopedViewSet, get_active_membership

from .models import Activity, WorkflowState
from .serializers import ActivitySerializer, WorkflowStateSerializer


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


class ActivityViewSet(OrganizationScopedViewSet):
    queryset = Activity.objects.select_related("status", "property").prefetch_related(
        "species"
    )
    serializer_class = ActivitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(property_id=property_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            organization=self.get_organization(), created_by=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
