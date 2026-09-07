"""Tests for the feedback pull endpoints' bearer-token gate.

These exist because of a specific defect (D9, 2026-09-07):
`ensure_feedback_token` compared the presented `Authorization` header with
`!=`. Python's string comparison returns as soon as it reaches a differing
byte, so how long the check takes is a function of how many leading bytes
a guess got right — the classic timing side channel on a secret compare.
The severity was low and is worth stating honestly: the endpoint is reached
over HTTPS across the public internet, where network jitter swamps the
nanoseconds involved. But the correct comparison costs one import, so there
was no reason to leave the weaker one in a secret-checking path.

`test_the_comparison_is_constant_time` is the one that actually pins the
fix. Every other test here passes just as well against the pre-fix `!=`,
because a timing side channel is invisible to a functional assertion — no
input distinguishes the two implementations by *result*, only by duration.
Rather than write a flaky wall-clock benchmark, that test asserts the
mechanism directly: the module must route its comparison through
`django.utils.crypto.constant_time_compare`.

The rest of the file is not redundant, though, and its most important
assertion is `test_an_unset_token_denies_everything`: "no token configured"
must mean *deny*, never "any request is fine". That invariant is the whole
reason this endpoint can be safely deployed to an instance that hasn't
provisioned a token, it is one `if not token` away from inverting, and
until now nothing asserted it.

Run with: python manage.py test apps.feedback
"""

from unittest import mock

from django.test import TestCase, override_settings

from apps.accounts.models import Organization
from apps.feedback import auth as feedback_auth
from apps.feedback.models import Feedback

TOKEN = "s3cret-feedback-token-value"

PULL_URL = "/api/feedback/pull/"
MARK_SYNCED_URL = "/api/feedback/pull/mark-synced/"


@override_settings(FEEDBACK_API_TOKEN=TOKEN)
class FeedbackPullTokenTests(TestCase):
    """The bearer-token gate on the two cross-org pull endpoints."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.item = Feedback.objects.create(
            organization=self.org,
            message="The map is slow on my phone.",
            status=Feedback.Status.NEW,
        )

    def _pull(self, header=None):
        kwargs = {"HTTP_AUTHORIZATION": header} if header is not None else {}
        return self.client.get(PULL_URL, **kwargs)

    # --- the fix itself -------------------------------------------------

    def test_the_comparison_is_constant_time(self):
        """The one assertion that fails against the pre-fix code.

        A timing channel has no functional symptom, so this pins the
        mechanism rather than a result: the token check must go through
        `constant_time_compare`. If someone later "simplifies" it back to
        `==`/`!=`, every other test here still passes and this one does
        not.
        """
        with mock.patch.object(
            feedback_auth, "constant_time_compare", wraps=feedback_auth.constant_time_compare
        ) as spy:
            self._pull(f"Bearer {TOKEN}")

        self.assertEqual(
            spy.call_count,
            1,
            "ensure_feedback_token must compare the bearer token with "
            "constant_time_compare, not a plain string comparison.",
        )
        presented, expected = spy.call_args.args
        self.assertEqual(presented, f"Bearer {TOKEN}")
        self.assertEqual(expected, f"Bearer {TOKEN}")

    # --- the gate still behaves exactly as it did -----------------------

    def test_the_correct_token_is_accepted(self):
        response = self._pull(f"Bearer {TOKEN}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.json()], [self.item.id])

    def test_a_missing_header_is_denied(self):
        self.assertEqual(self._pull().status_code, 403)

    def test_a_wrong_token_of_the_same_length_is_denied(self):
        """Same length, one byte different — the shape a timing attack
        walks through, and the case a length-only check would let by."""
        wrong = TOKEN[:-1] + ("x" if TOKEN[-1] != "x" else "y")
        self.assertEqual(len(wrong), len(TOKEN))

        self.assertEqual(self._pull(f"Bearer {wrong}").status_code, 403)

    def test_a_correct_prefix_is_denied(self):
        """Guards against a comparison that degrades to a prefix match."""
        self.assertEqual(self._pull(f"Bearer {TOKEN[:8]}").status_code, 403)

    def test_the_token_without_the_bearer_scheme_is_denied(self):
        self.assertEqual(self._pull(TOKEN).status_code, 403)

    def test_an_empty_header_is_denied_rather_than_crashing(self):
        """`Authorization: ` with no value must be a clean 403, not a 500.

        `constant_time_compare` is given a normalized string precisely so
        a missing or empty header can't reach it as `None`.
        """
        self.assertEqual(self._pull("").status_code, 403)

    def test_mark_synced_is_gated_by_the_same_check(self):
        """The write endpoint, not just the read one — it is the half that
        changes state, and it is easy to gate one and forget the other."""
        denied = self.client.post(
            MARK_SYNCED_URL,
            {"ids": [self.item.id]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {TOKEN}-wrong",
        )

        self.assertEqual(denied.status_code, 403)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Feedback.Status.NEW)

        allowed = self.client.post(
            MARK_SYNCED_URL,
            {"ids": [self.item.id]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {TOKEN}",
        )

        self.assertEqual(allowed.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, Feedback.Status.SYNCED)


class FeedbackUnsetTokenTests(TestCase):
    """An unconfigured token must deny everything.

    This is the load-bearing invariant of the whole module and the one
    that would be catastrophic to invert: most of this project's
    deployments have never provisioned `HABITAT_FEEDBACK_TOKEN`, so if an
    empty setting ever came to mean "skip the check", every one of them
    would be serving other organizations' feedback to anonymous callers.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        Feedback.objects.create(
            organization=self.org, message="hi", status=Feedback.Status.NEW
        )

    @override_settings(FEEDBACK_API_TOKEN="")
    def test_an_unset_token_denies_everything(self):
        self.assertEqual(self.client.get(PULL_URL).status_code, 403)
        self.assertEqual(
            self.client.get(PULL_URL, HTTP_AUTHORIZATION="Bearer ").status_code, 403
        )
        self.assertEqual(
            self.client.get(PULL_URL, HTTP_AUTHORIZATION="Bearer anything").status_code,
            403,
        )

    @override_settings(FEEDBACK_API_TOKEN="")
    def test_an_unset_token_denies_the_write_endpoint_too(self):
        response = self.client.post(
            MARK_SYNCED_URL,
            {"ids": []},
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer ",
        )

        self.assertEqual(response.status_code, 403)
