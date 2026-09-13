from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.blobs import defer_theme_image

from .models import Notification
from .serializers import NotificationSerializer


def _readable(user):
    """The caller's own notifications, loaded the way this app's
    serializer actually reads them.

    `select_related("organization")` is required — `NotificationSerializer`
    renders `organization.name`, and without it that is one extra query per
    notification. But joining to Organization drags in its
    `theme_header_image` blob, and Django rebuilds a `select_related`
    target per row rather than deduping it, so a 5 MB org banner would be
    loaded once for every notification in the list. That is D27 exactly,
    reintroduced by the join this attribution needs — see
    apps/accounts/blobs.py, which is why `defer_theme_image` takes a path
    to defer *through*. Nothing downstream of here reads those bytes.
    """
    return defer_theme_image(
        Notification.objects.filter(recipient=user).select_related("task", "organization"),
        "organization",
    )


@api_view(["GET"])
def notification_list(request):
    """The current user's own notifications, newest first. Unlike almost
    every other endpoint in the app, this is scoped to the *recipient*
    directly rather than an active organization (see org_scoping.py) — a
    notification is inherently personal, and (once a user can belong to
    more than one organization — still "first membership wins" today, see
    org_scoping.py's module docstring) should show up regardless of which
    org happens to be active.

    That is why the serializer carries the organization: this is the one
    list in the app whose rows may not belong to the org the caller is
    currently acting in, so it is the one list that has to say which org
    each row *is* from. See NotificationSerializer's docstring."""
    return Response(NotificationSerializer(_readable(request.user), many=True).data)


@api_view(["POST"])
def notification_mark_read(request, pk):
    notification = get_object_or_404(_readable(request.user), pk=pk)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return Response(NotificationSerializer(notification).data)


@api_view(["POST"])
def notification_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response(status=204)
