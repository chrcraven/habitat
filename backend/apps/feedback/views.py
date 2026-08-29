"""
In-app feedback: submission (any org member), an admin's own-org review
list, and the cross-org retrieval surface an external scheduled routine
uses to pull unreviewed feedback into the project's own build workflow.
See models.py's module docstring and /docs/open-questions.md ("App
feedback / build workflow") for the decided shape.
"""

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Membership
from apps.accounts.org_scoping import ensure_role, get_active_membership

from .auth import ensure_feedback_token
from .models import Feedback
from .serializers import FeedbackPullSerializer, FeedbackSerializer


@api_view(["GET"])
def feedback_config(request):
    """Whether the feature is turned on at all (HABITAT_FEEDBACK_ENABLED /
    settings.FEEDBACK_ENABLED) — the frontend calls this to decide whether
    to render the floating feedback button, so a deployment with the
    feature off (e.g. prod) shows nothing rather than a button that 404s
    on submit. Any logged-in member can check this; it reveals nothing
    beyond an on/off flag."""
    return Response({"enabled": settings.FEEDBACK_ENABLED})


@api_view(["GET", "POST"])
def feedback_list_or_submit(request):
    """POST: any org member submits feedback (decided 2026-08-29 — every
    member, not just admins). GET: admin-only, this org's own submitted
    feedback, so an admin can see and resolve what's been sent without
    querying the database directly — distinct from the cross-org
    `feedback_pull` below, which the external routine uses instead."""
    membership = get_active_membership(request.user)
    if membership is None:
        return Response({"detail": "You are not a member of any organization yet."}, status=404)

    if request.method == "POST":
        if not settings.FEEDBACK_ENABLED:
            return Response({"detail": "Feedback isn't enabled on this instance."}, status=404)
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"detail": "Feedback message is required."}, status=400)
        feedback = Feedback.objects.create(
            organization=membership.organization,
            submitted_by=request.user,
            message=message,
        )
        return Response(FeedbackSerializer(feedback).data, status=201)

    ensure_role(request.user, Membership.Role.ADMIN)
    items = Feedback.objects.filter(organization=membership.organization).select_related(
        "submitted_by"
    )
    return Response(FeedbackSerializer(items, many=True).data)


@api_view(["POST"])
def feedback_resolve(request, pk):
    """Admin marks their org's own feedback item resolved — independent
    of whether/when it was `synced` (see Feedback.Status's docstring)."""
    membership = get_active_membership(request.user)
    if membership is None:
        return Response({"detail": "You are not a member of any organization yet."}, status=404)
    ensure_role(request.user, Membership.Role.ADMIN)
    feedback = get_object_or_404(Feedback, pk=pk, organization=membership.organization)
    feedback.status = Feedback.Status.RESOLVED
    feedback.resolved_at = timezone.now()
    feedback.save(update_fields=["status", "resolved_at"])
    return Response(FeedbackSerializer(feedback).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def feedback_pull(request):
    """Cross-org retrieval for the external scheduled routine — bearer-
    token authenticated (see auth.py), not session-based, since the
    caller isn't a logged-in Habitat user at all. Defaults to
    `?status=new` so a repeated run only sees unhandled feedback (the
    incremental-fetch requirement); pass `?status=synced`/`resolved` to
    look at another bucket."""
    ensure_feedback_token(request)
    status_param = request.query_params.get("status", Feedback.Status.NEW)
    items = Feedback.objects.filter(status=status_param).select_related(
        "organization", "submitted_by"
    )
    return Response(FeedbackPullSerializer(items, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def feedback_mark_synced(request):
    """Marks the given feedback ids `synced` — i.e. "already recorded into
    build-questions.md, don't hand this to me again" — separate from
    `resolved`, which only an org admin sets once the underlying request
    is actually addressed (feedback_resolve above). Body: `{"ids": [...]}`.
    Only rows currently `new` are touched, so calling this twice with the
    same ids is harmless."""
    ensure_feedback_token(request)
    ids = request.data.get("ids") or []
    updated = Feedback.objects.filter(id__in=ids, status=Feedback.Status.NEW).update(
        status=Feedback.Status.SYNCED, synced_at=timezone.now()
    )
    return Response({"updated": updated})
