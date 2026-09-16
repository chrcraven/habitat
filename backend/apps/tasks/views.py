from apps.accounts.org_scoping import OrganizationScopedViewSet
from apps.accounts.query_params import int_query_param
from apps.notifications.events import notify
from apps.notifications.models import Notification

from .models import Task
from .serializers import TaskSerializer


def _assignment_message(task, actor):
    """The assignment notification's text: who assigned what.

    One function rather than the same f-string at the two call sites
    below, for the reason D6 and D34 both record: a string duplicated
    across sites is a string that drifts.

    The actor half is the point. `Notification` has no actor column — only
    `recipient` — so this message used to read *"You were assigned the
    task X."*, passive, with no way to tell who assigned it. Both call
    sites are holding `self.request.user` at that exact moment, so the app
    was stripping the actor out of the one push-style surface it has while
    the actor was in hand. That is D38 in miniature: attribution collected
    and discarded one layer before anyone could use it.

    Naming the actor by email follows the in-repo precedent
    (`Invitation.invited_by_email`, `Feedback.submitted_by_email`) and
    discloses nothing new — the recipient is a member of the same
    organization and can already enumerate member emails via
    `GET /api/org/members/`. See apps/accounts/attribution.py.

    Both callers already skip self-assignment, so this never renders
    "you assigned you". `message` is stored, so existing notifications
    keep their old wording — correct, since a notification is a record of
    what was said at the time.
    """
    return f'{actor.email} assigned you the task "{task.title}".'


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
        # `?status=` above is a CharField compare, so a nonsense value
        # just matches nothing; `?assigned_to=` is an id and reached the
        # database layer unparsed, which 500'd on a non-numeric — see
        # apps/accounts/query_params.py.
        assigned_to = int_query_param(self.request, "assigned_to")
        if assigned_to is not None:
            qs = qs.filter(assigned_to_id=assigned_to)
        return qs

    def perform_create(self, serializer):
        task = serializer.save(organization=self.get_organization(), created_by=self.request.user)
        if task.assigned_to_id and task.assigned_to_id != self.request.user.id:
            notify(
                organization=task.organization,
                recipient=task.assigned_to,
                verb=Notification.Verb.TASK_ASSIGNED,
                message=_assignment_message(task, self.request.user),
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
                message=_assignment_message(task, self.request.user),
                task=task,
            )
