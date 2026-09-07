"""
Bearer-token auth for the feedback *pull* endpoints (feedback_pull /
feedback_mark_synced in views.py) — see /docs/open-questions.md ("App
feedback / build workflow") for the full decision.

These two endpoints are called by an external scheduled routine (a Claude
Code session, the same shape as the one that queued this feature), not a
logged-in Habitat user — there's no session to authenticate with the way
everything else in the app does. A single shared secret is the simplest
shape that still satisfies the owner's hard requirement: the endpoint must
reject unauthenticated reads (feedback is not a public URL).

The secret itself is never committed here or anywhere else in the repo —
see settings.py's FEEDBACK_API_TOKEN and /docs/open-questions.md for where
it's actually provisioned (the target server's environment, and the
scheduled routine's own environment config on claude.ai — two places, kept
in sync by whoever sets this up, not by anything in this codebase).
"""

from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.exceptions import PermissionDenied


def ensure_feedback_token(request):
    """Raises PermissionDenied unless the request carries the correct
    `Authorization: Bearer <token>` header. Also denies everything if no
    token is configured at all — an empty/unset FEEDBACK_API_TOKEN must
    never mean "any request is fine"."""
    token = settings.FEEDBACK_API_TOKEN
    if not token:
        raise PermissionDenied("The feedback retrieval endpoint has no token configured.")
    # constant_time_compare, not `!=`: a plain string comparison returns as
    # soon as it hits a differing byte, so how long it takes leaks how much
    # of the secret a guess got right. The practical risk here is low (this
    # is reached over HTTPS across the internet, where jitter swamps the
    # difference), but the correct comparison costs one import — there is no
    # reason to leave the weaker one in a secret-checking path.
    presented = request.headers.get("Authorization") or ""
    if not constant_time_compare(presented, f"Bearer {token}"):
        raise PermissionDenied("Invalid or missing bearer token.")
