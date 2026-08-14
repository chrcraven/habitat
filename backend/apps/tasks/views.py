from apps.accounts.org_scoping import OrganizationScopedViewSet

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(OrganizationScopedViewSet):
    """Standard org-scoped CRUD (see org_scoping.py: viewer=read,
    editor=create/update — including status changes and reassignment,
    admin=delete). `?status=` and `?assigned_to=` filter the list, the
    same query-param pattern ActivityViewSet/SightingViewSet use for
    `?property=`."""

    queryset = Task.objects.select_related(
        "assigned_to", "created_by", "origin_sighting__species", "origin_activity"
    )
    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        assigned_to = self.request.query_params.get("assigned_to")
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)
        return qs

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization(), created_by=self.request.user)
