"""
Pluggable notification dispatch — see /docs/open-questions.md ("Task
assignee notification", decided 2026-08-29): in-app is the only channel
today, but this is built behind a channel abstraction so email (once real
SMTP is picked — see "Real email delivery isn't configured") or any other
future channel can be added by appending to CHANNELS, not by reworking
whatever calls `notify()`.

Call `notify(...)` at the point an event actually happens (today: task
assignment, see apps/tasks/views.py#TaskViewSet) rather than writing
directly to Notification/an email API — that indirection is the whole
point of this module.
"""

from .models import Notification


class Channel:
    """A notification channel's contract — subclass and implement `send`."""

    def send(self, *, organization, recipient, verb, message, task=None):
        raise NotImplementedError


class InAppChannel(Channel):
    """Writes a Notification row (see models.py) — read via
    GET /api/notifications/ and surfaced as a badge in the frontend nav.
    The only channel that exists today."""

    def send(self, *, organization, recipient, verb, message, task=None):
        Notification.objects.create(
            organization=organization,
            recipient=recipient,
            verb=verb,
            message=message,
            task=task,
        )


# Enabled channels, in dispatch order. Deliberately just the one for now —
# see the module docstring for how a future EmailChannel would plug in.
CHANNELS = [InAppChannel()]


def notify(*, organization, recipient, verb, message, task=None):
    """Fan an event out to every enabled channel. `recipient=None` (e.g. a
    task being unassigned) is a no-op, not an error — there's no one to
    notify."""
    if recipient is None:
        return
    for channel in CHANNELS:
        channel.send(
            organization=organization,
            recipient=recipient,
            verb=verb,
            message=message,
            task=task,
        )
