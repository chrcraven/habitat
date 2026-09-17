"""Rate limits for the two unauthenticated endpoints that run a password
hash (D40 — see /docs/open-questions.md, "Tech / infrastructure").

**Why these two endpoints and no others.** Habitat's six other limits are
all per-request *size* caps (`MAX_PHOTO_BYTES`, `MAX_LOGO_PIXELS`,
`CUSTOM_PAGE_HTML_MAX_BYTES`, …). None of them bounds a *rate*, and until
this module existed the word "throttle" appeared nowhere in the backend.
That was survivable everywhere except here, because `login_view` and
`signup` are the only unauthenticated paths that run a deliberately-slow
key-derivation function:

  - Django 5.2's default hasher is pbkdf2_sha256 at 1,000,000 iterations.
    Measured on this repo's pinned Django (median of 8): ~582 ms to check
    a password, ~584 ms to make one. That is under two attempts per second
    per core.
  - `ModelBackend.authenticate` runs `UserModel().set_password(password)`
    when the user does **not** exist — deliberately, to flatten the timing
    difference (Django #20760). So the full hash is paid for *any* email:
    no account, no valid address and no knowledge of the instance are
    needed. ~400 request bytes buy ~600 ms of server CPU.

**And the inversion that makes this different from every other resource
finding in this repo.** D17 was fixed by bounding the resource — cap the
pixels, decode less. This one cannot be, because the expense *is* the
security control: a cheaper hash is weaker password storage for every
user. Bounding the rate is the only remedy. Do not "optimise" the hasher.

The other two password-hashing paths are deliberately absent from this
module and must not be added to it: `password_reset_confirm` and
`invitation_accept` each require a `secrets.token_urlsafe(32)` — 256 bits
— so they are protected by entropy, not by rate, and throttling them would
lock a legitimate invitee out of a link they hold. `password_reset_request`
runs no hash at all; its own (separate, older) abuse vector is recorded in
the 2026-08-27 task log.
"""

import math

from rest_framework.exceptions import Throttled
from rest_framework.throttling import SimpleRateThrottle

#: Requests per window, per client address. Both are stated here as
#: constants rather than buried in settings so that changing one is a
#: deliberate edit with this reasoning in front of it — the same treatment
#: `MAX_PHOTO_BYTES` and `MAX_THEME_IMAGE_BYTES` already get.
#:
#: LOGIN_RATE — 10 a minute costs an attacker's address at most ~6 seconds
#: of server CPU per minute, while leaving a person who is fumbling a
#: password roughly three times the attempts they actually need before
#: they give up and use the reset flow. Tighter would start refusing real
#: people; looser stops bounding anything, since the interesting attack is
#: sustained rather than bursty.
LOGIN_RATE = "10/min"
#: SIGNUP_RATE — an order of magnitude stricter, because a signup is not
#: just a hash. It writes 14 rows (User, Organization, Membership, 3
#: WorkflowStates, 8 ActivityTypes from the two seeding receivers), there
#: is no email verification anywhere, and **nothing in the app can ever
#: remove them**: there is no OrganizationViewSet, no account closure and
#: no user-deletion path outside Django admin. Every signup is permanent,
#: unverified and free, so the limit is sized for real humans (who sign up
#: once) rather than for retries.
SIGNUP_RATE = "5/hour"


class _Throttled(Throttled):
    """DRF's 429, carrying our sentence instead of ours *plus* DRF's.

    `Throttled.__init__` appends its own "Expected available in N
    seconds." to whatever detail it is given, whenever `wait` is not None.
    Passing both therefore produces a refusal that states the wait time
    twice, in two different registers:

        "Too many sign-in attempts from this device. Try again in about
         58 seconds. If you've forgotten your password, use the reset link
         on the sign-in page. Expected available in 58 seconds."

    Found by reading a real response off a real server, not by a failing
    assertion — every test written for this message passed against it,
    because they check that the advice is *present*, which it is. Worth
    keeping in mind when writing the next test about wording.

    `wait` is assigned after the fact rather than passed in, because
    assigning it is all the base class does with it besides the append,
    and DRF's exception handler reads `exc.wait` to set `Retry-After`.
    """

    def __init__(self, wait, detail):
        super().__init__(wait=None, detail=detail)
        self.wait = math.ceil(wait) if wait else None


class _AddressRateThrottle(SimpleRateThrottle):
    """Throttle by client address, for everyone, authenticated or not.

    Two deliberate departures from the DRF classes it would be natural to
    reach for:

    1. **Not `AnonRateThrottle`.** That class returns None — no throttling
       at all — as soon as `request.user` is authenticated. These
       endpoints are `AllowAny` and a request carrying a session cookie
       reaches them exactly as an anonymous one does, so inheriting that
       bypass would leave a free, unlimited path to the same hash.
    2. **Not `ScopedRateThrottle`.** That reads its scope off a
       `throttle_scope` attribute of the *view*, and these views are
       `@api_view` functions, which have no clean place to hang one. A
       subclass with a fixed `scope` is the same mechanism with the
       indirection removed.

    **The key is the address and must stay the address.** Keying on the
    submitted email is the attractive wrong fix and is worthless: the
    email is a free-text field of the request being limited, so an
    attacker varies it per request and is never throttled at all, while a
    real user — who types the same address every time — is. Tests pin this
    from both directions.
    """

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }

    def throttle_failure(self):
        """Refuse with wording a locked-out person can act on.

        DRF's own refusal ("Request was throttled. Expected available in N
        seconds.") is accurate and reads like a fault in the site. A limit
        tight enough to matter will sometimes catch someone who simply
        mistyped their password, and the failure mode this repo keeps
        finding is a control that looks broken rather than refused (D13,
        D21) — so the message names what happened, when to come back, and
        the way out that does not require waiting.

        Raising here rather than returning False is what lets the message
        be ours: `APIView.check_throttles` calls `self.throttled(request,
        wait)`, which raises DRF's stock `Throttled`, and an `@api_view`
        function has no `self` to override. The exception is a `Throttled`
        subclass, so DRF's default handler still answers 429 and still
        sets `Retry-After`.
        """
        wait = self.wait()
        raise _Throttled(wait=wait, detail=self.refusal_detail(wait))

    def refusal_detail(self, wait):
        raise NotImplementedError


def _retry_phrase(wait):
    """"in about 30 seconds" / "in about 2 minutes" — never "in 0 seconds".

    `wait` is a float and can be a fraction of a second at the boundary,
    which rounds to a refusal telling someone to retry immediately. The
    floor of one second is there for that case.
    """
    seconds = max(1, int(wait or 0) + 1)
    if seconds < 90:
        return f"in about {seconds} second{'' if seconds == 1 else 's'}"
    minutes = (seconds + 59) // 60
    return f"in about {minutes} minute{'' if minutes == 1 else 's'}"


class LoginRateThrottle(_AddressRateThrottle):
    # `rate` set directly rather than via DEFAULT_THROTTLE_RATES: it keeps
    # the number beside the measurement that justifies it, and keeps
    # settings.py from having to import an app module before the app
    # registry is loaded. `scope` still names the cache bucket.
    scope = "login"
    rate = LOGIN_RATE

    def refusal_detail(self, wait):
        return (
            "Too many sign-in attempts from this device. "
            f"Try again {_retry_phrase(wait)}. "
            'If you have forgotten your password, the "Forgot your password?" '
            "link still works."
        )


class SignupRateThrottle(_AddressRateThrottle):
    scope = "signup"
    rate = SIGNUP_RATE

    def refusal_detail(self, wait):
        return (
            "Too many accounts have been created from this device recently. "
            f"Try again {_retry_phrase(wait)}. "
            "If you already have an account, sign in instead."
        )
