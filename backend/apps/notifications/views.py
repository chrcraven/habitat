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


#: How many notifications a single list response may carry.
#:
#: This is the *whole* fix for the transfer half of D30, so it is worth
#: knowing why it is this number. NotificationsBell renders every row this
#: endpoint returns and nothing else consumes the list, so the bound and
#: the number of rows a user can actually see are the same quantity —
#: deliberately, because the bug was that they were not. Before this, the
#: endpoint returned *every* notification the recipient had ever received
#: (they are never purged: the repo's one management command is for
#: properties) to render 20 rows, every 60 seconds, on every authenticated
#: screen — 143 MB per 8-hour day at 1,000 lifetime notifications, whether
#: or not anyone ever opened the dropdown.
#:
#: Raising this costs bandwidth on every poll for every user; it is not a
#: free knob. If the bell ever needs to show more, raise it here and the
#: client follows, rather than growing a second number on the client.
NOTIFICATION_LIST_LIMIT = 20


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
    each row *is* from. See NotificationSerializer's docstring.

    Returns `{"results": [...], "unread_count": N}` rather than a bare
    array, and the second half is not decoration — it is what makes
    bounding the first half *safe*. The unread badge used to be derived on
    the client by counting unread rows in the response, which is only
    correct while the response is the complete history. Bounding the list
    without sending a count would leave a user with 60 unread seeing "20",
    in a response that looks perfectly well-formed — the same class as
    D28, where the client was not failing to display something but was
    never being sent it. So the count is computed here, over *all* the
    caller's unread notifications, unaffected by the bound.
    """
    readable = _readable(request.user)
    return Response(
        {
            "results": NotificationSerializer(
                readable[:NOTIFICATION_LIST_LIMIT], many=True
            ).data,
            # Deliberately a separate COUNT(*) over the unbounded set, not
            # a count of `results`. Cheap (an indexed count, no rows
            # fetched) and it is the only reason the bound above is not a
            # silent regression of the badge.
            "unread_count": readable.filter(is_read=False).count(),
        }
    )


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
