"""
Helper for the "forgot password" flow — same shape as invitations.py (see
that module's docstring), because it has the same underlying gap: no real
email infrastructure is decided yet (/docs/open-questions.md, "Hosting/ops
model"), so `settings.EMAIL_BACKEND` defaults to the console backend and
the message never reaches a real inbox in dev (or in this sandbox).

Unlike an invitation, though, there's no admin-facing UI here to fall back
on for copying the link out of band — this is a self-service, unauthenticated
flow, and showing the reset link directly in the API response would turn
"did you get my email" into a user-enumeration oracle (a response that
only carries a real link when the address has an account). So the reset
URL is *only* ever written to the (console, for now) email backend, never
returned to the caller — see views.py#password_reset_request's always-200
response. Configure EMAIL_BACKEND/EMAIL_HOST/etc. via env vars for a
deployment that should actually deliver mail; until then, this flow is
only really exercisable by reading the dev server's console output.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def reset_url(token):
    return f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{token}/"


def send_password_reset_email(reset):
    """Best-effort, same reasoning as send_invitation_email: a
    misconfigured/unreachable SMTP server shouldn't turn "request a
    reset" into a 500, and the caller already gets a generic success
    response regardless (see module docstring)."""
    url = reset_url(reset.token)
    try:
        send_mail(
            subject="Reset your Habitat password",
            message=(
                f"Someone (hopefully you) asked to reset the password for "
                f"{reset.user.email} on Habitat.\n\n"
                f"Reset it here: {url}\n\n"
                f"This link expires in "
                f"{int(reset.EXPIRY.total_seconds() // 3600)} hour(s) and can "
                f"only be used once. If you didn't request this, you can "
                f"ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reset.user.email],
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            "Couldn't send password reset email to %s.",
            reset.user.email,
            exc_info=True,
        )
