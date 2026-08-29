from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


@api_view(["GET"])
def notification_list(request):
    """The current user's own notifications, newest first. Unlike almost
    every other endpoint in the app, this is scoped to the *recipient*
    directly rather than an active organization (see org_scoping.py) — a
    notification is inherently personal, and (once a user can belong to
    more than one organization — still "first membership wins" today, see
    org_scoping.py's module docstring) should show up regardless of which
    org happens to be active."""
    notifications = Notification.objects.filter(recipient=request.user).select_related("task")
    return Response(NotificationSerializer(notifications, many=True).data)


@api_view(["POST"])
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return Response(NotificationSerializer(notification).data)


@api_view(["POST"])
def notification_mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return Response(status=204)
