"""Who created, last edited or linked a record — and the one rule that
keeps surfacing it from republishing a member's email to the open
internet.

Habitat has recorded attribution since Phase 1. `Activity.created_by`,
`Activity.updated_by`, `Sighting.created_by`, `Page.created_by`,
`SightingActivityLink.linked_by`, `Task.created_by`,
`Invitation.invited_by` and `Feedback.submitted_by` are all written on
every relevant call site. For most of the project's life exactly one of
them (`Feedback.submitted_by`) ever reached a human — so the app could
tell you who complained about a button and not who redrew the boundary
of a restoration site. See D38 in /docs/open-questions.md.

The sharpest version of the gap was a matched pair split one line apart:
`ActivitySerializer.Meta.fields` carried `created_at` and `updated_at`
and neither `created_by` nor `updated_by`. **The timestamp travelled and
the person didn't.**

# The rule

**Attribution never lives on a base serializer.** It lives on a
`…WithAttribution` subclass, and only an authenticated, org-scoped view
may name that subclass.

That is not style. `apps/public_site/views.py` serves
`ActivitySerializer` and `SightingSerializer` to `AllowAny` (see
`property_activities` and `property_sightings`), so **every field on
those serializers travels to anonymous visitors**. Adding
`created_by_email` to either `Meta.fields` publishes a real person's
email address on every public activity and sighting — which is D8
verbatim (a nameless signup publishing the signing-up user's email),
re-entered through a different door.

What makes it dangerous rather than merely wrong is that it is
**invisible in the diff**: the change is two lines in
`apps/activities/serializers.py` and the consequence lands in
`apps/public_site/`, a different app, with nothing in the edited file
mentioning it. Same family as D27/D28 — the invariant is a property of
each *response*, not of the model, so it is not self-maintaining.

# Three ways to get this wrong, all of which look right

1. **Put the fields on the base serializer.** Every authenticated
   response is then correct, and the public site starts publishing
   emails. An outcome test on the authenticated path passes. Only a test
   that reads the *public* payload catches it.

2. **Strip the fields in `apps/public_site/`.** This passes both of
   those tests and is still the wrong shape, because it is an *opt-out*:
   the next public endpoint someone adds inherits the leak by default
   and has to remember to opt out again. Caught only by a mechanism test
   asserting the base serializer does not declare the fields at all —
   which is what `assert_no_attribution` below exists for.

3. **Emit the fields as null on the public path** (a context flag on one
   shared serializer). No email leaks, but the public payload's shape
   now advertises that attribution exists and is being withheld, and the
   flag is one forgotten keyword argument away from case 1. Caught by a
   test that pins the public payload's exact key set.

The subclass shape is chosen because it fails in the safe direction: a
new *public* endpoint that reuses the base serializer gets no
attribution (correct), and a new *authenticated* endpoint that reuses
the base serializer gets no attribution either (a missing feature, not a
disclosure). The only way to leak is to import a class with
"WithAttribution" in its name into a view decorated `AllowAny`, which is
legible in a diff in a way that two extra strings in a `fields` list is
not. D27's lesson, applied: put the decision where the decision is made
— and here the decision is "who is this response for?", which is made by
the view.

# Why email, and why a viewer may see it

`Invitation.invited_by_email` and `Feedback.submitted_by_email` are the
in-repo precedent for labelling a person by email, so this follows them
rather than inventing a display-name convention.

Showing it to any member — including a viewer — discloses nothing new:
`MembershipViewSet.list` carries no `ensure_role` (unlike `create` and
`partial_update` beside it), so any member can already enumerate every
other member's email through `GET /api/org/members/`. That was audited
and is intentional; it is the premise that makes this safe, and it
should not be rediscovered as a defect.

# Deleted users

All the underlying FKs are `on_delete=SET_NULL`, and there is no
user-deletion path in the app (only Django admin), so in practice these
are stable. `None` is a real possible value all the same, and every
field below serializes it as `null` rather than raising — the frontend
renders "unknown", the same fallback the Feedback row already uses.
"""

from rest_framework import serializers

# The fields each subclass adds, kept here rather than spelled out per
# serializer so the three call sites can't drift the way D6's
# content-type check did when it was copy-pasted four times.
CREATED_BY = "created_by_email"
UPDATED_BY = "updated_by_email"
LINKED_BY = "linked_by_email"


def attribution_field(source):
    """One `…_by_email` field.

    `default=None` rather than `allow_null=True`: the source walks a
    nullable FK (`created_by.email`), and without a default DRF raises
    rather than serializing null when the FK is unset. Matches how
    `TaskSerializer.created_by_email` and
    `InvitationSerializer.invited_by_email` already declare theirs.
    """
    return serializers.CharField(source=source, read_only=True, default=None)


# The `select_related` a list endpoint needs once it serves attribution.
#
# Without it each row costs its own query for the user, on endpoints that
# D30/D31 measured as this app's volume problem (org-wide and
# unpaginated). With it, note that a `select_related` target is rebuilt
# per row and Django does not dedupe it — which is exactly how D27
# happened — so this is only safe because `User` carries **no**
# `BinaryField`. It has `email`, two name fields, three flags and a
# timestamp. If a blob is ever added to `User`, every query listed in
# `apps/accounts/blobs.py` has to gain a defer for it and so does this.
# A test pins that (`apps/accounts/tests.py`, D38 section).
ACTIVITY_RELATED = ("created_by", "updated_by")
SIGHTING_RELATED = ("created_by",)
LINK_RELATED = ("linked_by",)


def assert_no_attribution(serializer_class):
    """True when `serializer_class` declares no attribution field.

    Exists to be called from tests against the **base** serializers, so
    that wrong fix (2) above — stripping the fields in `public_site`
    instead of never declaring them — goes red instead of shipping
    quietly. A strip leaves the fields declared here, which is the only
    observable difference between it and the real fix: the public
    response body is identical either way.
    """
    declared = set(serializer_class().fields)
    return not (declared & {CREATED_BY, UPDATED_BY, LINKED_BY})
