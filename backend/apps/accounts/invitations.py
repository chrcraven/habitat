"""
Helpers shared between the Invitation serializer and the views that create/
accept invitations — kept in one place so the accept-link URL is built
identically everywhere (the org admin portal's "copy link" fallback, the
email body, and the API's own accept_url field all have to agree).

No real email infrastructure is decided yet (see /docs/open-questions.md,
"Hosting/ops model") — `settings.EMAIL_BACKEND` defaults to Django's
console backend, which just logs the message instead of delivering it, so
in dev (and in this sandbox) the message body never actually reaches an
inbox. That's why `accept_url` is also returned directly in the API
response and shown in the org admin UI: an admin without real SMTP
configured can still copy/paste the link and share it out of band, the
same way the old admin-sets-a-password flow worked. Configure
EMAIL_BACKEND/EMAIL_HOST/etc. via env vars for a deployment that should
actually deliver the email.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def accept_url(token):
    return f"{settings.FRONTEND_URL.rstrip('/')}/accept-invite/{token}/"


def send_invitation_email(invitation):
    """Best-effort — a misconfigured/unreachable SMTP server shouldn't turn
    "create an invitation" into a 500. Errors are logged, not raised; the
    accept_url is always returned to the caller regardless (see module
    docstring) so the invite is still usable even if this silently fails.
    """
    inviter = invitation.invited_by.email if invitation.invited_by else "An admin"
    url = accept_url(invitation.token)
    try:
        send_mail(
            subject=f"You're invited to join {invitation.organization.name} on Habitat",
            message=(
                f"{inviter} invited you to join {invitation.organization.name} on "
                f"Habitat as a {invitation.get_role_display()}.\n\n"
                f"Accept the invitation: {url}\n\n"
                f"This link expires in {invitation.EXPIRY.days} days."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
    except Exception:
        logger.warning(
            "Couldn't send invitation email to %s — share the accept link manually.",
            invitation.email,
            exc_info=True,
        )
