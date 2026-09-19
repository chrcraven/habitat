"""Running the email validation this project already declares.

`User.email` and `Invitation.email` are both `models.EmailField`, which
carries Django's own `EmailValidator`. That validator had **never run**.
Model-field validators fire only from `full_clean()`, which `save()` does
not call and which appears zero times in this backend; the usual second
line of defence is a serializer's `EmailField`, and there isn't one either,
because all four entry points read the address straight off the request
body. So every address Habitat stores was whatever string the caller sent:
measured on the pinned Django, `not an email`, `chris@`, `@example.com`,
`a@b@c.com`, `<script>alert(1)</script>` and an address carrying an embedded
newline all became real, permanent accounts, each invalid per the validator
already attached to that very field.

The browser is not the missing check. `<input type="email">` refuses the
malformed garbage above and **accepts every case that actually happens to a
person** — `chris@gmial.com` (transposed), `chris@example.co` (dropped
letter), `chris@gmial` (HTML5 email validation does not require a TLD) and
someone else's real address. The protection and the real-world failure mode
barely overlap.

**The rule this module follows: validate where an address is *stored*;
normalize everywhere, and leave the paths that merely *look one up* alone.**

* **Stored** — `signup` (creates `User.email`) and `MembershipViewSet.create`
  (creates `Invitation.email`, which `invitation_accept` then copies into a
  `User` verbatim, so validating at invitation time covers acceptance too).
  These call `clean_stored_email`.
* **Looked up** — `login_view` and `password_reset_request`. These call
  `normalize_email` and validate nothing, deliberately, for two reasons that
  both cut the same way. They create nothing, so there is nothing to keep
  clean. And rows written *before* this module existed may hold a malformed
  address: refusing one at login would lock that account out of the only
  path still open to it, and refusing one at password reset would lock it
  out of recovery. A guard that bricks the accounts it was added to protect
  is worse than the gap.

  `password_reset_request` additionally has to stay byte-identical whatever
  it is handed — that is D22's anti-enumeration property, and the cheapest
  way to keep it true is to have no branch at all.

**Normalization is centralized even though validation is not**, and that is
the point of `normalize_email` existing as its own function. `strip().lower()`
was correct at all four sites, but only by four separate coincidences:
`BaseUserManager.normalize_email` lowercases the *domain* alone, and
`EmailField(unique=True)` is case-sensitive in Postgres, so a single site
dropping `.lower()` would produce either two accounts for one person or an
account that can never be logged into. One function makes that structural
instead of coincidental.

**The length check is not redundant with the format validator**, and the
reason is easy to get backwards. `EmailValidator.__call__` refuses anything
over **320** characters (RFC 3696); the column is `max_length=254`. So the
band from 255 to 320 is accepted by the validator and too long for the
column — and on real Postgres that is not a tidy failure but
`DataError: value too long for type character varying(254)`, which is not an
`IntegrityError`, is caught nowhere in this backend and has no DRF handler:
an unhandled 500.

Beware the witness. A 312-character local part looks like the obvious
example and is useless as one: it totals 324 characters, so the *validator*
refuses it and a test built on it passes against a fix that has no length
check at all — measured, not reasoned. Any example here has to assert the
two properties that make it an example (longer than 254, shorter than 320),
or it silently stops testing what it was chosen to test.

**Length is checked first**, which keeps a regex off an unbounded string —
the ordering D17 established for image decoding, applied to text: measure
before doing the work the measurement exists to prevent.

What this module does **not** do is prove an address is *reachable*.
`chris@gmial.com` passes everything here. Whether signup should verify the
address is an open owner question (D40b's Q1) — format validity is not
reachability, and one is not evidence of the other.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email as validate_email_format

from .models import Invitation, User

# Derived from the field rather than restated, so the guard cannot drift
# from the column it protects. A test pins that Invitation.email agrees, so
# taking the limit from one field stays safe for both.
MAX_EMAIL_LENGTH = User._meta.get_field("email").max_length

EMAIL_REQUIRED_DETAIL = "Email is required."
EMAIL_TOO_LONG_DETAIL = (
    f"An email address can be at most {MAX_EMAIL_LENGTH} characters."
)


def normalize_email(raw):
    """Fold an incoming address into the one form this app stores.

    No validation — callers that look an address up want exactly this and
    nothing more (see the module docstring on why login and password reset
    deliberately stop here).
    """
    return (raw or "").strip().lower()


def clean_stored_email(raw):
    """Normalize an address that is about to be written to a column, and
    run the validation its field already declares.

    Returns the normalized address. Raises Django's `ValidationError`, which
    every caller already knows how to turn into a 400 — the same idiom these
    views use for `validate_password`.

    Deliberately validates the **field**, not the model: `full_clean()`
    would also enforce `unique=True`, replacing signup's own deliberate
    "An account with that email already exists." with Django's wording and
    moving a message that sits on this project's enumeration surface.
    """
    email = normalize_email(raw)
    if not email:
        raise DjangoValidationError(EMAIL_REQUIRED_DETAIL)
    if len(email) > MAX_EMAIL_LENGTH:
        raise DjangoValidationError(EMAIL_TOO_LONG_DETAIL)
    validate_email_format(email)
    return email
