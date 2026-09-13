"""Tests for the one list in this app that is deliberately *not* scoped to
the caller's active organization.

Every other read endpoint derives its queryset from
`get_active_membership`, so "which organization is this row about?" is
answered by the request itself and never has to be said. `notification_list`
filters on the recipient alone, on purpose — a notification is personal and
should reach you whichever org is active. The consequence nobody had traced
(D28, /docs/open-questions.md) is that it is therefore the one payload whose
organization is *not* implied, and it was not being sent one: a two-org
user's bell showed another organization's task titles with nothing naming
that organization.

Two unrelated invariants are pinned here, in two clearly-separated
sections, because fixing the first is what put the second at risk:

1. **Attribution travels.** The organization's id *and* name are on the
   wire, and the recipient-only filter still holds (it is a feature, not
   an oversight — so a "fix" that org-scopes this list must go red).

2. **The attribution did not reintroduce D27.** Rendering the org's name
   requires `select_related("organization")`, and Organization carries a
   `theme_header_image` blob which Django rebuilds *per row* across a
   join. Writing the obvious join without `defer_theme_image` would load a
   5 MB banner once per notification while returning byte-identical JSON.
   Section 2 is the only thing that can tell those two apart.
"""

import re

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import Membership, Organization, User
from apps.tasks.models import Task

from .models import Notification
from .views import _readable

PASSWORD = "pw-12345678"


def _selected_columns(queryset, prefix):
    """Whole column names matching `prefix`, never a substring search.

    D27 left this trap behind and it is worth not re-stepping in:
    `"theme_header_image" in sql` is True even when the blob is deferred,
    because `theme_header_image_content_type` contains it — an assertion
    that looks like it checks something and cannot fail.
    """
    return set(re.findall(rf'"({prefix}\w*)"', str(queryset.query)))


class NotificationAttributionTests(TestCase):
    """Section 1 — the organization a notification belongs to reaches the
    client. Pre-fix, the payload was id/verb/message/task/task_title/
    is_read/created_at: the client was not failing to *display* the
    attribution, it was never sent it."""

    def setUp(self):
        # Two organizations, one user in both. `Membership.Meta.ordering`
        # is ["created_at", "id"] and get_active_membership takes .first(),
        # so `home` is deliberately created first: it is the active one,
        # and `elsewhere` is the org whose notifications the bell shows but
        # whose tasks the app cannot reach. That asymmetry is the defect.
        self.home = Organization.objects.create(name="Home Prairie")
        self.elsewhere = Organization.objects.create(name="Far Meadow")
        self.user = User.objects.create_user(email="member@example.com", password=PASSWORD)
        Membership.objects.create(
            organization=self.home, user=self.user, role=Membership.Role.ADMIN
        )
        Membership.objects.create(
            organization=self.elsewhere, user=self.user, role=Membership.Role.EDITOR
        )
        self.client.force_login(self.user)

    def _notify(self, organization, title):
        task = Task.objects.create(
            organization=organization, title=title, assigned_to=self.user
        )
        return Notification.objects.create(
            organization=organization,
            recipient=self.user,
            verb=Notification.Verb.TASK_ASSIGNED,
            message=f'You were assigned the task "{title}".',
            task=task,
        )

    def test_a_notification_carries_its_organization_id_and_name(self):
        """The core of D28. Both fields, not one: the id is what the client
        compares against the active membership to decide whether a row is
        from elsewhere, and the name is what it renders. Sending only the
        name would force a string comparison against a mutable label."""
        self._notify(self.home, "Mow the swale")

        row = self.client.get("/api/notifications/").json()[0]

        self.assertEqual(row["organization"], self.home.id)
        self.assertEqual(row["organization_name"], "Home Prairie")

    def test_a_notification_from_another_organization_names_that_organization(self):
        """The actual reported scenario: a task assigned in the org the
        user is *not* currently acting in. Pre-fix this row was
        indistinguishable from one belonging to the active org, which is
        what made the bell unattributable — the message carries the other
        org's task title verbatim."""
        self._notify(self.elsewhere, "Pull garlic mustard")

        row = self.client.get("/api/notifications/").json()[0]

        self.assertEqual(row["organization"], self.elsewhere.id)
        self.assertEqual(row["organization_name"], "Far Meadow")
        self.assertNotEqual(
            row["organization"],
            self.home.id,
            "the row must be attributable to the org it belongs to, not the active one",
        )
        # The half that makes it a defect rather than a curiosity: the
        # title on screen belongs to a task /tasks cannot list.
        self.assertIn("Pull garlic mustard", row["message"])

    def test_both_organizations_appear_correctly_attributed_in_one_list(self):
        """The mixed list is the state a two-org user is actually in, and
        the one where a per-request org would have been wrong."""
        self._notify(self.home, "Mow the swale")
        self._notify(self.elsewhere, "Pull garlic mustard")

        rows = self.client.get("/api/notifications/").json()
        by_name = {r["organization_name"]: r for r in rows}

        self.assertEqual(set(by_name), {"Home Prairie", "Far Meadow"})
        self.assertEqual(by_name["Home Prairie"]["organization"], self.home.id)
        self.assertEqual(by_name["Far Meadow"]["organization"], self.elsewhere.id)

    def test_marking_one_read_returns_the_same_attribution(self):
        """The detail response feeds the same component, so it must carry
        the same fields — a client that re-renders from this response
        must not lose the attribution it just had."""
        notification = self._notify(self.elsewhere, "Pull garlic mustard")

        row = self.client.post(f"/api/notifications/{notification.id}/read/").json()

        self.assertTrue(row["is_read"])
        self.assertEqual(row["organization"], self.elsewhere.id)
        self.assertEqual(row["organization_name"], "Far Meadow")

    def test_the_session_payload_names_the_active_organization(self):
        """Passes both pre- and post-fix, deliberately.

        The app chrome now renders `membership.organization.name` to answer
        "which organization am I in?" — the name was always delivered and
        never displayed. This pins the *delivery*, so a later tidy-up that
        trims the session payload to ids makes this go red instead of
        silently blanking the only place the app names the org."""
        payload = self.client.get("/api/auth/me/").json()

        self.assertEqual(payload["membership"]["organization"]["name"], "Home Prairie")
        self.assertEqual(payload["membership"]["organization"]["id"], self.home.id)

    def test_the_list_is_still_scoped_to_the_recipient_and_not_to_an_org(self):
        """Passes both ways by design — it guards the *other* direction.

        The tempting over-correction for D28 is to org-scope this list so
        the attribution problem disappears. That would be wrong: a
        notification is personal, and scoping it would silently hide the
        other org's notifications instead of labelling them. This test
        fails if someone "fixes" D28 that way."""
        self._notify(self.home, "Mow the swale")
        self._notify(self.elsewhere, "Pull garlic mustard")

        rows = self.client.get("/api/notifications/").json()

        self.assertEqual(
            len(rows),
            2,
            "both organizations' notifications must still reach their recipient — "
            "this list is scoped to the person, not the active organization",
        )

    def test_another_users_notification_is_neither_listed_nor_markable(self):
        """No IDOR. Passes both ways; it exists because the fix rewrote the
        `get_object_or_404` lookup into a queryset filter, and that rewrite
        is exactly where the recipient check could have been dropped."""
        other = User.objects.create_user(email="other@example.com", password=PASSWORD)
        Membership.objects.create(
            organization=self.home, user=other, role=Membership.Role.EDITOR
        )
        theirs = Notification.objects.create(
            organization=self.home,
            recipient=other,
            verb=Notification.Verb.TASK_ASSIGNED,
            message="Not yours.",
        )

        self.assertEqual(self.client.get("/api/notifications/").json(), [])

        response = self.client.post(f"/api/notifications/{theirs.id}/read/")

        self.assertEqual(response.status_code, 404)
        theirs.refresh_from_db()
        self.assertFalse(theirs.is_read, "another user's notification must not be marked read")


class NotificationListDoesNotLoadImageBytesTests(TestCase):
    """Section 2 — the attribution must not reintroduce D27.

    Unrelated to section 1's subject, and here anyway because they are
    causally linked: naming the organization requires joining to it, and
    that join is what puts the banner blob back on the read path. Both
    plausible-but-wrong implementations return byte-identical JSON, so
    only these two tests separate them — and each is blind to what the
    other catches:

      * `select_related("organization")` with no `defer_theme_image`
        → caught only by the column test; the query count stays constant.
      * `organization_name` with no `select_related` at all
        → caught only by the query-count test; no blob appears in the SQL.
    """

    def setUp(self):
        self.org = Organization.objects.create(
            name="Banner Org",
            theme_header_image=b"\x89PNG\r\n\x1a\n" + b"banner" * 64,
            theme_header_image_content_type="image/png",
        )
        self.user = User.objects.create_user(email="banner@example.com", password=PASSWORD)
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.client.force_login(self.user)

    def _add_notifications(self, count):
        for i in range(count):
            Notification.objects.create(
                organization=self.org,
                recipient=self.user,
                verb=Notification.Verb.TASK_ASSIGNED,
                message=f"Assigned thing {i}.",
            )

    def test_the_notification_list_does_not_select_the_banner_blob(self):
        """The anti-naive-join test.

        Django does not dedupe a `select_related` target across rows, so
        without the deferral a themed org's banner is rebuilt once per
        notification — D27's exact shape, reached through the join this
        attribution needed. The response body is identical either way.
        """
        columns = _selected_columns(_readable(self.user), "theme_header_image")

        self.assertNotIn(
            "theme_header_image",
            columns,
            "the notification list selects the org's banner bytes; with select_related "
            "they are loaded once per notification",
        )

    def test_the_notification_list_does_select_the_column_it_actually_reads(self):
        """The deferral must be surgical. If a later change reaches for
        `.only(...)` instead, the org's *name* stops being loaded and
        Django answers each row's `organization.name` with its own query —
        byte-identical JSON, one query per row."""
        columns = _selected_columns(_readable(self.user), "name")

        self.assertIn(
            "name",
            columns,
            "the notification list no longer loads the organization's name — "
            "it will be fetched per row",
        )

    def _list_query_count(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, 200)
        return len(ctx.captured_queries), len(response.json())

    def test_listing_many_notifications_costs_a_constant_number_of_queries(self):
        """The anti-N+1 test, and the only one that catches an attribution
        added with no join at all.

        Counts *all* queries rather than grepping for a column name —
        D27's own lesson: its first query-count test filtered for the blob
        column while the naive fix's per-row lookups were for the column
        beside it, so the test passed against the very fix it existed to
        reject.
        """
        self._add_notifications(1)
        one_row, count = self._list_query_count()
        self.assertEqual(count, 1)

        self._add_notifications(12)
        thirteen_rows, count = self._list_query_count()
        self.assertEqual(count, 13)

        self.assertEqual(
            thirteen_rows,
            one_row,
            f"listing 13 notifications took {thirteen_rows} queries where listing 1 took "
            f"{one_row} — the per-row growth means the organization is being fetched "
            "once per notification rather than joined",
        )
