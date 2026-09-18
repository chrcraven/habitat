"""
One Django system check: refuse to let a mail *server* configuration sit
silently behind a transport that ignores it.

Why this exists (D45, /build-questions.md 2026-09-19). `settings.py` reads
six email variables, and exactly one of them — `EMAIL_BACKEND` — chooses
the transport. Habitat defaults it to Django's *console* backend, so an
operator who sets `EMAIL_HOST` and credentials and nothing else gets a
deployment that delivers no mail at all. What makes that worth a check
rather than a doc note alone is that **every visible signal reports
success**: `send_mail` under the console backend returns 1 and raises
nothing, so both senders in this package (`password_reset.py`,
`invitations.py`) take their happy path, and the container log — the one
place an operator debugging "did my reset email go out?" actually looks —
prints a complete, well-formed RFC-822 message carrying their own
configured From address, the right recipient, subject and body. The only
tells are `@localhost` in the Message-ID and the fact that it is in a log.

**It also inverts stock Django, which is why the operator most likely to
get this wrong is the one who already knows Django.** Measured on the
pinned 5.2.17: `django.conf.global_settings.EMAIL_BACKEND` is the *smtp*
backend, so in an ordinary Django project setting `EMAIL_HOST` and
credentials genuinely is how you configure mail. Here it is not.

Three things about the shape of this check are load-bearing, because each
is a plausible-looking change that would quietly make it useless. All
three were built and measured (table in /build-questions.md):

1. **It keys on `EMAIL_HOST`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`
   only** — never on `EMAIL_PORT`, `EMAIL_USE_TLS` or
   `DEFAULT_FROM_EMAIL`. Those three have non-empty defaults (587, True,
   noreply@habitat.local), so treating them as evidence the operator
   configured a mail server makes this fire on *every* deployment,
   including every default one. A warning that is always on is a warning
   nobody reads.
2. **It compares against the console backend specifically**, not
   `!= smtp`. Django's test runner swaps in the locmem backend, so the
   looser comparison warns on every test run and every CI job.
3. **It is NOT registered as a deployment check.** That is the tempting
   one — this reads like a deployment concern, and `Tags.security` +
   `deploy=True` looks more correct. But `manage.py check` (what CI runs)
   and `manage.py migrate` (what `entrypoint.sh` runs on every backend
   container start) both skip deployment checks, which is exactly how D7
   survived for the life of the project. Deploy-tagging it would leave it
   invisible in the only log the operator is reading. Registered plainly,
   the warning prints to stderr during `migrate` at every boot, directly
   above the convincing fake email — and still exits 0, so it does not
   turn a mail misconfiguration into a crashloop.

Deliberately NOT covered: `EMAIL_BACKEND=smtp` with no `EMAIL_HOST`. That
misconfiguration announces itself — a real send against an unreachable
server raises, and both senders log a warning plus traceback (measured:
Python's last-resort handler prints it, since Habitat sets no `LOGGING`).
This check exists for the silent case, not the loud one.

Whether a production boot should refuse to start on the console backend at
all is a separate, open owner decision (D45b's Q2) — a warning here does
not pre-empt it.
"""

from django.conf import settings
from django.core.checks import Warning as CheckWarning, register

CONSOLE_BACKEND = "django.core.mail.backends.console.EmailBackend"
SMTP_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#: Settings that only a person intending to deliver real mail would set.
#: See point 1 in the module docstring before adding to this tuple — the
#: other three email settings have non-empty defaults and belong nowhere
#: near it.
MAIL_SERVER_SETTINGS = ("EMAIL_HOST", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD")

INERT_MAIL_CONFIG_ID = "habitat.W001"


@register()
def check_mail_transport_is_not_inert(app_configs, **kwargs):
    """Warn when a mail server is configured but the console backend is
    still selected, so the configuration is silently ignored."""
    configured = [name for name in MAIL_SERVER_SETTINGS if getattr(settings, name, "")]
    if not configured or settings.EMAIL_BACKEND != CONSOLE_BACKEND:
        return []
    return [
        CheckWarning(
            "Habitat is configured with mail server settings (%s) but "
            "EMAIL_BACKEND is still Django's console backend, so no email is "
            "delivered — messages are written to this log instead. Password "
            "reset and organization invitation emails will appear to send "
            "successfully and will never arrive." % ", ".join(configured),
            hint=(
                "Set EMAIL_BACKEND=%s to deliver mail, or unset %s if this "
                "deployment is deliberately console-only. Note that Django's "
                "own default is the smtp backend; Habitat overrides it to "
                "console, so the mail server settings alone are not enough."
                % (SMTP_BACKEND, ", ".join(configured))
            ),
            id=INERT_MAIL_CONFIG_ID,
        )
    ]
