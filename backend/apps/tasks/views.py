from apps.accounts.org_scoping import OrganizationScopedViewSet
from apps.notifications.events import notify
from apps.notifications.models import Notification

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(OrganizationScopedViewSet):
    """Standard org-scoped CRUD (see org_scoping.py: viewer=read,
    editor=create/update — including status changes and reassignment,
    admin=delete). `?status=` and `?assigned_to=` filter the list, the
    same query-param pattern ActivityViewSet/SightingViewSet use for
    `?property=`.

    Assigning (create with `assigned_to` set) or reassigning (update
    changing `assigned_to`) a task dispatches an in-app notification to
    the new assignee — see /docs/open-questions.md ("Task assignee
    notification", decided 2026-08-29) and apps/notifications/events.py
    for the pluggable-channel dispatch this goes through.
    """

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
        task = serializer.save(organization=self.get_organization(), created_by=self.request.user)
        if task.assigned_to_id and task.assigned_to_id != self.request.user.id:
            notify(
                organization=task.organization,
                recipient=task.assigned_to,
                verb=Notification.Verb.TASK_ASSIGNED,
                message=f'You were assigned the task "{task.title}".',
                task=task,
            )

    def perform_update(self, serializer):
        previous_assignee_id = serializer.instance.assigned_to_id
        task = serializer.save()
        if (
            task.assigned_to_id
            and task.assigned_to_id != previous_assignee_id
            and task.assigned_to_id != self.request.user.id
        ):
            notify(
                organization=task.organization,
                recipient=task.assigned_to,
                verb=Notification.Verb.TASK_ASSIGNED,
                message=f'You were assigned the task "{task.title}".',
                task=task,
            )
