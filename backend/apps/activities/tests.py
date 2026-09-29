"""Regression tests for apps.activities.

**One organization's species must never reach another organization's
activity** (D12, found and fixed 2026-09-08) — this repo's bar for a
checked-in test being "this already regressed silently once".

The defect: `ActivitySpeciesSerializer` left `species` writable, so it was
an auto-generated `PrimaryKeyRelatedField` over the *whole* Species table,
and `activity_species_detail`'s PATCH passed `data=request.data` with no
serializer context and no organization check.

The sharpest way to hold it is that **the two halves of one endpoint
disagreed**. The POST path in that same view resolves the species with
`get_object_or_404(Species, id=..., organization=activity.organization)`
and rejected precisely the id the PATCH path 24 lines below accepted. So
`test_post_rejects_another_orgs_species` and
`test_patch_cannot_move_a_link_to_another_orgs_species` are deliberately
a pair: the first pins the behaviour that was always correct, the second
the one that now matches it. Reading either alone understates the finding.

Why it survived the 2026-09-01 cross-org FK pass, worth knowing before
assuming the class of bug is now impossible: that session fixed
`ActivitySerializer.property/status/activity_type` and
`SightingSerializer.property/species`, all on `ModelViewSet`s. This one
lives in a *through-model* serializer driven by a function-based view.

Three consequences are pinned, because the disclosure one is easy to
under-rate: the foreign species' **name** came back in the PATCH response
and would then be republished through `ActivitySerializer.species_names`,
which the public site serves unauthenticated; and because the FK is
`PROTECT`, the row also blocked the owning org from deleting its *own*
species through a row it could neither see nor delete.

Two tests here pass against the pre-fix code by design and are not
redundant — they guard against a "fix" that breaks the endpoint instead of
fixing it (`test_role_quantity_and_detail_still_save`) or that quietly
stops honouring the org check on the way in
(`test_post_accepts_own_orgs_species`). The test that actually fails
against pre-fix code is the PATCH pair.

Run with: python manage.py test apps.activities
"""

import json
import threading
import time

from django.contrib.gis.geos import Polygon
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext

from apps.accounts.models import Membership, Organization, Property, User
from apps.activities.models import Activity, ActivitySpecies, WorkflowState
from apps.sightings.models import SightingActivityLink
from apps.species.models import Species


def make_org(name, email):
    """An org plus an editor in it. Organization creation seeds the default
    WorkflowState/ActivityType rows via post_save, so an activity can be
    built without configuring a workflow first."""
    org = Organization.objects.create(name=name)
    user = User.objects.create_user(email=email, password="pw-12345678")
    Membership.objects.create(
        organization=org, user=user, role=Membership.Role.EDITOR
    )
    return org, user


def make_activity(org):
    prop = Property.objects.create(
        organization=org,
        name=f"{org.name} Property",
        boundary=Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
    )
    return Activity.objects.create(
        organization=org,
        property=prop,
        activity_type=org.activity_types.first(),
        status=org.workflow_states.first(),
        geometry=Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
    )


class ActivitySpeciesStaysInsideTheOrganizationTests(TestCase):
    def setUp(self):
        self.org, self.user = make_org("Mine", "mine@example.com")
        self.other_org, _ = make_org("Theirs", "theirs@example.com")

        self.activity = make_activity(self.org)
        self.mine = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )
        self.theirs = Species.objects.create(
            organization=self.other_org, common_name="Their Secret Orchid"
        )
        self.link = ActivitySpecies.objects.create(
            activity=self.activity, species=self.mine, role="planted", quantity=3
        )
        self.client.force_login(self.user)

    def detail_url(self):
        return f"/api/activities/{self.activity.id}/species/{self.link.id}/"

    # --- The defect ---

    def test_patch_cannot_move_a_link_to_another_orgs_species(self):
        """The core of D12. Pre-fix this validated, saved, and returned the
        other organization's species."""
        self.client.patch(
            self.detail_url(),
            data={"species": self.theirs.id},
            content_type="application/json",
        )
        self.link.refresh_from_db()
        self.assertEqual(
            self.link.species_id,
            self.mine.id,
            "an editor must not be able to attach another organization's "
            "species to their own activity",
        )

    def test_patch_response_does_not_disclose_the_other_orgs_species_name(self):
        """The disclosure half. `species_name` is what
        ActivitySerializer.species_names would go on to republish through
        the unauthenticated public site."""
        response = self.client.patch(
            self.detail_url(),
            data={"species": self.theirs.id},
            content_type="application/json",
        )
        self.assertNotContains(
            response, "Their Secret Orchid", status_code=response.status_code
        )

    def test_the_other_org_can_still_delete_its_own_species(self):
        """The cross-tenant denial. `ActivitySpecies.species` is PROTECT, so
        a smuggled row would block the owning org from deleting a species
        through a row it cannot see."""
        self.client.patch(
            self.detail_url(),
            data={"species": self.theirs.id},
            content_type="application/json",
        )
        self.theirs.delete()
        self.assertFalse(Species.objects.filter(id=self.theirs.id).exists())

    def test_patch_ignores_the_species_field_entirely(self):
        """Read-only means read-only, not "validated": even a *same-org*
        species id is ignored rather than applied. Pins the actual semantics
        so the next reader doesn't expect a re-pointing API that isn't
        there — changing an activity's species is remove-and-re-add through
        the POST path."""
        other_mine = Species.objects.create(
            organization=self.org, common_name="Butterfly Weed"
        )
        self.client.patch(
            self.detail_url(),
            data={"species": other_mine.id},
            content_type="application/json",
        )
        self.link.refresh_from_db()
        self.assertEqual(self.link.species_id, self.mine.id)

    # --- Guards against a fix that breaks the endpoint ---

    def test_role_quantity_and_detail_still_save(self):
        """Passes both before and after the fix, deliberately. The endpoint's
        actual job must survive making one field read-only."""
        response = self.client.patch(
            self.detail_url(),
            data={"role": "treated_target", "quantity": 12, "detail": "foliar"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.link.refresh_from_db()
        self.assertEqual(self.link.role, "treated_target")
        self.assertEqual(self.link.quantity, 12)
        self.assertEqual(self.link.detail, "foliar")

    def test_patch_with_species_alongside_real_edits_still_applies_the_edits(self):
        """A read-only field must be ignored, not rejected — otherwise a
        client that sends the whole object back would start failing."""
        response = self.client.patch(
            self.detail_url(),
            data={"species": self.theirs.id, "quantity": 7},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.link.refresh_from_db()
        self.assertEqual(self.link.quantity, 7)
        self.assertEqual(self.link.species_id, self.mine.id)

    # --- The POST half, which was always correct ---

    def test_post_rejects_another_orgs_species(self):
        """Half of the pair that states the finding: this rejected the exact
        id the PATCH path accepted."""
        response = self.client.post(
            f"/api/activities/{self.activity.id}/species/",
            data={"species": self.theirs.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_post_accepts_own_orgs_species(self):
        response = self.client.post(
            f"/api/activities/{self.activity.id}/species/",
            data={"species": Species.objects.create(
                organization=self.org, common_name="Little Bluestem"
            ).id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)


# ---------------------------------------------------------------------------
# D18 — the "already linked" guard had nothing in the database behind it
# (found and fixed 2026-09-10)
#
# `activity_species_list`'s POST rejects a duplicate species on an activity
# with a 400, but it does so through `get_or_create`, whose body is
# `get() except DoesNotExist: create() except IntegrityError: get()` — an
# unlocked SELECT-then-INSERT. That is only race-safe when a unique
# constraint can reject the loser's INSERT, and `ActivitySpecies.Meta`
# carried only `verbose_name_plural`. Without the constraint the recovery
# branch is *unreachable*: two concurrent POSTs both SELECT nothing, both
# INSERT successfully, and the endpoint answers 201 twice. The guard failed
# open, and the damage stuck — a duplicated pair makes `get_or_create`'s own
# `get()` raise `MultipleObjectsReturned`, which is not an `APIException`
# and has no custom `EXCEPTION_HANDLER`, so it reached users as a 500 that
# never cleared on its own.
#
# **Why the pairing below, and not outcome tests alone.** This is the D16
# lesson generalised by D17: the two concurrency tests can pass against
# broken code on a machine where the requests happen to serialise, and they
# would pass equally against the plausible-but-wrong fix — an
# application-level `.exists()` re-check with no constraint, which closes
# the window it happens to test while leaving the race itself open. So they
# are paired with *mechanism* tests that assert the database itself refuses
# the duplicate. Only those catch the wrong fix.
#
# Four tests here pass both before and after by design, and say so: they
# guard against a "fix" that stops the endpoint doing its real job.
# ---------------------------------------------------------------------------


class ActivitySpeciesDuplicateRaceTests(TransactionTestCase):
    """TransactionTestCase, not TestCase: the race only exists across real
    committed transactions, and TestCase would wrap the whole test in one
    and make it disappear.

    The interleaving is forced rather than hoped for, and the real
    `get_or_create` and the real endpoint are used throughout. The barrier
    sits in `ActivitySpecies.save()`, which is the INSERT — so both requests
    are held there until each has already run its own SELECT and found
    nothing. That is exactly the window the missing constraint left open,
    and it is the interleaving two simultaneous POSTs actually produce."""

    def setUp(self):
        self.org, self.user = make_org("Racing", "racing@example.com")
        self.activity = make_activity(self.org)
        self.species = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )

    def _add_concurrently(self):
        original_save = ActivitySpecies.save
        barrier = threading.Barrier(2, timeout=30)

        def save_holding_at_the_insert(instance, *args, **kwargs):
            # Only an INSERT waits. get_or_create's IntegrityError recovery
            # path re-reads rather than saving, so the barrier is reached
            # exactly twice.
            if instance.pk is None:
                barrier.wait()
            return original_save(instance, *args, **kwargs)

        results = {}

        def add(label):
            try:
                client = Client()
                client.force_login(self.user)
                response = client.post(
                    f"/api/activities/{self.activity.id}/species/",
                    data=json.dumps({"species": self.species.id, "role": "planted"}),
                    content_type="application/json",
                )
                results[label] = response.status_code
            except Exception as exc:  # a 500 surfaces here as the raised error
                results[label] = repr(exc)
            finally:
                from django.db import connections

                connections.close_all()

        ActivitySpecies.save = save_holding_at_the_insert
        try:
            threads = [
                threading.Thread(target=add, args=("first",)),
                threading.Thread(target=add, args=("second",)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=45)
            for thread in threads:
                self.assertFalse(thread.is_alive(), "a request deadlocked")
        finally:
            ActivitySpecies.save = original_save
            from django.db import connection as default_connection

            default_connection.close()

        return results

    def test_two_concurrent_adds_leave_exactly_one_row(self):
        """The defect itself. Pre-fix both requests return 201 and the pair
        ends up with two rows, after which every later POST for it is a
        500."""
        results = self._add_concurrently()

        rows = ActivitySpecies.objects.filter(
            activity=self.activity, species=self.species
        ).count()
        self.assertEqual(
            rows,
            1,
            "a species must never be linked to one activity twice: "
            f"concurrent adds returned {sorted(map(str, results.values()))} "
            f"and left {rows} rows",
        )

    def test_exactly_one_of_the_two_adds_is_refused(self):
        """The other half: the single row isn't luck, it's the guard firing
        on the second request because the database refused its INSERT."""
        results = self._add_concurrently()

        self.assertEqual(
            sorted(str(value) for value in results.values()),
            ["201", "400"],
            "one add should succeed and the other be refused with the "
            f"endpoint's own 400, got {results}",
        )

    def test_the_endpoint_still_works_after_the_race(self):
        """The persistent-damage half of D18, and the reason it earned a
        record: pre-fix the duplicate row left behind made the *next* POST
        for that pair a 500 that never cleared on its own."""
        self._add_concurrently()

        client = Client()
        client.force_login(self.user)
        response = client.post(
            f"/api/activities/{self.activity.id}/species/",
            data=json.dumps({"species": self.species.id}),
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            400,
            "a later add for the same pair must be the honest 400, not a 500",
        )


class ActivitySpeciesConstraintMechanismTests(TestCase):
    """The tests that catch the plausible-but-wrong fix.

    An application-level `.exists()` re-check in the view would satisfy every
    outcome test above while leaving the race wide open, because nothing in
    the database would stop the second INSERT. These assert the constraint
    itself, so that "fix" goes red."""

    def setUp(self):
        self.org, self.user = make_org("Mechanism", "mechanism@example.com")
        self.activity = make_activity(self.org)
        self.species = Species.objects.create(
            organization=self.org, common_name="Little Bluestem"
        )
        self.link = ActivitySpecies.objects.create(
            activity=self.activity, species=self.species, role="planted"
        )

    def test_the_database_itself_refuses_a_duplicate_pair(self):
        """The load-bearing assertion. This bypasses the view entirely — no
        application-level check can make it pass."""
        with self.assertRaises(IntegrityError) as raised:
            with transaction.atomic():
                ActivitySpecies.objects.create(
                    activity=self.activity, species=self.species, role="other"
                )
        self.assertIn("unique_activity_species", str(raised.exception))

    def test_get_or_create_recovers_instead_of_creating_a_second_row(self):
        """The constraint is what hands get_or_create back its recovery
        branch — this is the line the view's 400 actually depends on."""
        link, created = ActivitySpecies.objects.get_or_create(
            activity=self.activity, species=self.species, defaults={"role": "other"}
        )
        self.assertFalse(created, "get_or_create must report the existing row")
        self.assertEqual(link.id, self.link.id)
        self.assertEqual(
            ActivitySpecies.objects.filter(
                activity=self.activity, species=self.species
            ).count(),
            1,
        )

    def test_the_constraint_is_declared_on_the_model(self):
        """Pins the declaration, so removing it has to change a test that
        says why it exists."""
        names = {
            constraint.name: getattr(constraint, "fields", None)
            for constraint in ActivitySpecies._meta.constraints
        }
        self.assertIn("unique_activity_species", names)
        self.assertEqual(tuple(names["unique_activity_species"]), ("activity", "species"))

    def test_a_duplicate_that_somehow_exists_degrades_to_400_not_500(self):
        """Defence in depth for the branch the constraint should make
        unreachable. MultipleObjectsReturned inherits straight from
        Exception, so with no custom EXCEPTION_HANDLER it would otherwise
        reach the user as a 500."""
        from apps.activities import views as activities_views

        def raise_multiple(*args, **kwargs):
            raise ActivitySpecies.MultipleObjectsReturned(
                "get() returned more than one ActivitySpecies -- it returned 2!"
            )

        original = ActivitySpecies.objects.get_or_create
        ActivitySpecies.objects.get_or_create = raise_multiple
        try:
            self.client.force_login(self.user)
            response = self.client.post(
                f"/api/activities/{self.activity.id}/species/",
                data={"species": self.species.id},
                content_type="application/json",
            )
        finally:
            ActivitySpecies.objects.get_or_create = original

        self.assertEqual(response.status_code, 400)
        self.assertIn("already linked", response.json()["detail"])

    def test_the_sibling_link_model_still_has_its_constraint(self):
        """SightingActivityLink is the model that always got this right, and
        it is why D18 was findable at all. If it ever loses its constraint,
        the same defect reappears at two more call sites."""
        names = {
            constraint.name for constraint in SightingActivityLink._meta.constraints
        }
        self.assertIn("unique_sighting_activity_link", names)


class ActivitySpeciesStillDoesItsJobTests(TestCase):
    """These pass both before and after the fix, deliberately. They exist so
    that "delete the feature" or "refuse everything" isn't a passing fix."""

    def setUp(self):
        self.org, self.user = make_org("Working", "working@example.com")
        self.activity = make_activity(self.org)
        self.species = Species.objects.create(
            organization=self.org, common_name="Butterfly Weed"
        )
        self.client.force_login(self.user)

    def url(self):
        return f"/api/activities/{self.activity.id}/species/"

    def test_a_species_can_still_be_linked(self):
        response = self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_adding_the_same_species_twice_in_a_row_is_still_refused(self):
        """The sequential path, which always worked — and is why nobody
        noticed the concurrent one didn't."""
        first = self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        second = self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        self.assertEqual((first.status_code, second.status_code), (201, 400))

    def test_a_different_species_is_still_accepted(self):
        """The constraint is on the pair, not on the activity — an activity
        must still be able to carry several species."""
        other = Species.objects.create(organization=self.org, common_name="Big Bluestem")
        self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        response = self.client.post(
            self.url(), data={"species": other.id}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivitySpecies.objects.filter(activity=self.activity).count(), 2)

    def test_removing_a_species_then_re_adding_it_still_works(self):
        """A unique constraint that outlived the row would make this fail —
        worth pinning, since it is the obvious way to get this wrong."""
        created = self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        link_id = created.json()["id"]
        deleted = self.client.delete(f"{self.url()}{link_id}/")
        self.assertEqual(deleted.status_code, 204)

        response = self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)

    def test_the_species_is_listed_once(self):
        """The smaller D18 symptom: `species_names` iterates the M2M through
        this table, and that field is served unauthenticated by the public
        site, so a duplicated pair rendered the species twice."""
        self.client.post(
            self.url(), data={"species": self.species.id}, content_type="application/json"
        )
        self.activity.refresh_from_db()
        self.assertEqual(
            [s.common_name for s in self.activity.species.all()], ["Butterfly Weed"]
        )


# ---------------------------------------------------------------------------
# D75 — three check-then-act guards with nothing holding between the check
# and the act (found and fixed 2026-09-29)
#
# D16 added this backend's only lock, `_lock_organization`, and gave it a
# docstring stating the *class* of defect in general terms: "count …, then
# demote/remove one — with nothing holding between the two. Two admins
# [acting] at the same moment therefore both read a count of 2, both pass,
# and both write."
#
# Three guards one app over matched that word for word and took nothing:
#
#   * `WorkflowStateViewSet.destroy`  — "needs at least one workflow state"
#   * `WorkflowStateViewSet.destroy`  — "your only state marked as finished"
#   * `WorkflowStateSerializer.validate` — the `is_done` un-flag guard
#
# So an organization could land with **zero** workflow states (an activity's
# status is required, so it can log no activity at all) or **zero**
# `is_done` states — which per that guard's own comment silently drives the
# public map's done-vs-planned layers, the dashboard's Recent/Upcoming split
# and the Activities status filter, leaving every activity reading as
# unfinished forever. D54's family: confidently wrong beats broken.
#
# **Why the cross-path test is the one that matters.** The two guards live
# in different entry points — one in a viewset method, one in a serializer
# reached through `update()` — so a fix that locks only the path it was
# looking at leaves the *other* pairing wide open. `test_deleting_one_done_
# state_while_another_is_un_flagged_…` races a DELETE against a PATCH, and
# is the only test here that a per-path lock fails.
#
# **The wrong-fix table, measured rather than predicted — and it corrected
# this comment twice.** Seven variants were built whole (D56: a ladder of
# single reverts certifies the broken combination as fine) and run against
# this section. Red out of 32:
#
#   not fixed at all                       6   the defect, verbatim
#   check, then lock, then act             6   inert; identical to no lock
#   lock taken after the whole write       6   inert; identical to no lock
#   `transaction.atomic()` and no lock     6   inert — see below
#   lock only `destroy`                    3   cross-path + un-flag + one mechanism
#   lock only `update`                     4   cross-path + both deletes + one mechanism
#   lock the state rows, not the org row   2   **both mechanism tests, nothing else**
#
# Two predictions in the first draft of this comment were wrong, both in the
# standing D38/D40/D45/D48 direction, and both are corrected here rather
# than in the memory of it:
#
# 1. It said the mechanism tests assert *ordering* because the attractive
#    wrong fix is "a lock taken after the guard has already read", which a
#    presence-only assertion would miss. Measured, that variant is not
#    subtle at all — taking the lock after the read serialises nothing, so
#    it fails every concurrency test too. **No broken variant is caught by
#    the ordering half alone.** The one variant it uniquely catches
#    (`read-hoisted-above-the-lock`, 1 red) leaves the real guard inside
#    the lock and is therefore *correct* — the assertion flags dead weight
#    there, not a defect. It is kept because it is deterministic where the
#    concurrency tests depend on a forced one-second interleaving, not
#    because anything measured needed it.
#
# 2. The genuinely dangerous variant is the one nobody named: **lock the
#    workflow-state rows instead of the organization row.** It passes every
#    behavioural test in this file — locking all of an org's states does
#    serialise these particular racers — and is caught *only* by the two
#    mechanism tests asserting the lock is on `accounts_organization`.
#    Delete those two and it ships green. It is still the wrong choice, for
#    a reason this repo has found three times already: it locks a *set*,
#    and `WorkflowState.Meta.ordering` is `["organization_id", "order"]`
#    with **no uniqueness constraint on `order`** (measured), so the
#    acquisition order between two transactions is undefined the moment two
#    states share an `order` — which the app permits. A non-total ORDER BY
#    (D2, D30, D70) inside a lock, where it reads as a deadlock and a 500.
#    An empty set also locks nothing, and a second serialisation point for
#    one organization's invariants is how a future guard takes the wrong
#    one. **Stated with its limit: the deadlock was not reproduced here** —
#    only the non-total ordering it needs was.
#
# The measured surprise worth keeping on its own: **`transaction.atomic()`
# with no lock is completely inert** (6 red, identical to doing nothing).
# "Make it atomic" reads as the fix for a race and, under read-committed
# with no lock, changes nothing at all.
#
# Four tests here pass both before and after by design and say so: a lock is
# a good way to break an endpoint, and the sequential guards, the ordinary
# delete and the ordinary edit all have to keep working.
#
# Deliberately NOT touched: `ActivityTypeViewSet.destroy` has no last-type
# guard at all (recorded as a near-miss 2026-09-12 and left there). That is a
# *missing* guard, not an unlocked one, and adding it here would be a
# different change wearing this one's clothes.
# ---------------------------------------------------------------------------


def make_admin_org(name, email):
    """An org plus an admin — `destroy` needs admin, `update` needs editor."""
    org = Organization.objects.create(name=name)
    user = User.objects.create_user(email=email, password="pw-12345678")
    Membership.objects.create(organization=org, user=user, role=Membership.Role.ADMIN)
    return org, user


def _two_plain_states(org):
    """Exactly two states, neither flagged.

    Built by clearing the seeded Planned/In Progress/Done set rather than
    working with it, because the seeded set cannot demonstrate this race:
    deleting `Done` is refused by the *second* guard (it is the only
    `is_done` state), so a concurrent pair drawn from it would be refused
    for the wrong reason and the test would pass against broken code."""
    org.workflow_states.all().delete()
    return (
        WorkflowState.objects.create(organization=org, name="Alpha", order=0),
        WorkflowState.objects.create(organization=org, name="Beta", order=1),
    )


def _two_done_states(org):
    """Exactly two states, both flagged finished — the fixture for the
    `is_done` half. A third, unflagged state keeps the *other* guard
    ("needs at least one workflow state") out of the way, so a refusal
    here can only have come from the guard under test."""
    org.workflow_states.all().delete()
    WorkflowState.objects.create(organization=org, name="Open", order=0)
    return (
        WorkflowState.objects.create(organization=org, name="Done", is_done=True, order=1),
        WorkflowState.objects.create(organization=org, name="Closed", is_done=True, order=2),
    )


class WorkflowStateGuardConcurrencyTests(TransactionTestCase):
    """TransactionTestCase, not TestCase: the race only exists across real
    committed transactions, and TestCase would wrap the whole test in one
    and make it disappear."""

    def setUp(self):
        self.org, self.admin = make_admin_org("Racers", "admin@example.com")
        # A second admin in the *same* org: the race needs two requests that
        # are each individually authorised, not one actor hitting the
        # endpoint twice.
        Membership.objects.create(
            organization=self.org,
            user=User.objects.create_user(email="second@example.com", password="pw-12345678"),
            role=Membership.Role.ADMIN,
        )
        self.second = User.objects.get(email="second@example.com")

    def _race(self, first, second):
        """Run two writes at once, forcing the interleaving that makes the
        race observable rather than hoping the scheduler produces it.

        The latch sits on the model's own **write** methods — not on the
        guard's read — and that placement is the whole point. Sleeping
        before the read would make the sleeper read *late*, i.e. after the
        other request had already committed, which is precisely the
        ordering the defect does not have: pre-fix, both requests read the
        pre-write state and only then write. Holding the first writer lets
        the second one read a state that is about to stop being true.

        `WorkflowState.delete` and `.save` are both patched from one shared
        latch so a DELETE and a PATCH can race each other, and both methods
        exist identically before and after the fix — so the same harness
        measures the red path without being rewritten for it.
        """
        state = {"seen": 0}
        state_lock = threading.Lock()
        real_delete = WorkflowState.delete
        real_save = WorkflowState.save

        def hold_first(real):
            def wrapper(self_, *args, **kwargs):
                with state_lock:
                    is_first = state["seen"] == 0
                    state["seen"] += 1
                if is_first:
                    time.sleep(1.0)
                return real(self_, *args, **kwargs)

            return wrapper

        results = {}

        def run(actor, label, request):
            try:
                client = Client()
                client.force_login(actor)
                results[label] = request(client)
            finally:
                from django.db import connections

                connections.close_all()

        WorkflowState.delete = hold_first(real_delete)
        WorkflowState.save = hold_first(real_save)
        try:
            threads = [
                threading.Thread(target=run, args=(self.admin, "first", first)),
                threading.Thread(target=run, args=(self.second, "second", second)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            for thread in threads:
                self.assertFalse(thread.is_alive(), "a request deadlocked")
        finally:
            WorkflowState.delete = real_delete
            WorkflowState.save = real_save
            connection.close()
        return results

    @staticmethod
    def _delete(state_id):
        return lambda client: client.delete(f"/api/workflow-states/{state_id}/").status_code

    @staticmethod
    def _unflag(state_id):
        return lambda client: client.patch(
            f"/api/workflow-states/{state_id}/",
            data=json.dumps({"is_done": False}),
            content_type="application/json",
        ).status_code

    def test_two_admins_deleting_the_last_two_states_cannot_empty_the_workflow(self):
        """The first defect. Pre-fix both requests return 204 and the
        organization is left with no workflow state at all, which means it
        can no longer log an activity."""
        alpha, beta = _two_plain_states(self.org)

        results = self._race(self._delete(alpha.id), self._delete(beta.id))

        self.assertGreaterEqual(
            self.org.workflow_states.count(),
            1,
            "an organization must never be left with zero workflow states: "
            f"concurrent deletes returned {sorted(results.values())}",
        )

    def test_exactly_one_of_the_two_deletes_is_refused(self):
        """The other half: the survivor isn't luck, it's the guard firing on
        the second request once it can see the first one's write."""
        alpha, beta = _two_plain_states(self.org)

        results = self._race(self._delete(alpha.id), self._delete(beta.id))

        self.assertEqual(
            sorted(results.values()),
            [204, 400],
            "one delete should succeed and the other be refused",
        )

    def test_two_admins_un_flagging_the_last_two_done_states_cannot_empty_them(self):
        """The serializer guard, raced. Pre-fix both PATCHes return 200 and
        the org keeps no state marked finished — after which every activity
        reads as unfinished everywhere `is_done` is consumed."""
        done, closed = _two_done_states(self.org)

        results = self._race(self._unflag(done.id), self._unflag(closed.id))

        self.assertGreaterEqual(
            self.org.workflow_states.filter(is_done=True).count(),
            1,
            "an organization must never be left with zero done-flagged states: "
            f"concurrent un-flags returned {sorted(results.values())}",
        )

    def test_deleting_one_done_state_while_another_is_un_flagged_cannot_empty_them(self):
        """The cross-path case, and the only test here that a per-path lock
        fails. The two guards live in different entry points — one in
        `WorkflowStateViewSet.destroy`, one in
        `WorkflowStateSerializer.validate` reached through `update()` — so
        locking whichever one a fix happened to be looking at leaves this
        pairing entirely open, with both requests still returning success."""
        done, closed = _two_done_states(self.org)

        results = self._race(self._delete(done.id), self._unflag(closed.id))

        self.assertGreaterEqual(
            self.org.workflow_states.filter(is_done=True).count(),
            1,
            "a delete racing an un-flag must not leave zero done-flagged states: "
            f"returned {sorted(results.values())}",
        )


class WorkflowStateGuardMechanismTests(TestCase):
    """Pins the mechanism, not the outcome — and specifically **which row**
    is locked, which measurement showed to be the load-bearing half.

    These assert two things. That the lock is on `accounts_organization`
    is the one that earns its place: the variant that locks the
    *workflow-state rows* instead passes every behavioural test in this
    file and is caught by nothing else (see the section header). That the
    lock comes *before* the guard's first read is cheaper insurance —
    measured, no broken variant needs it, because a lock taken after the
    read serialises nothing and therefore fails the concurrency tests
    too. It is kept because it is deterministic where those depend on a
    forced one-second interleaving.

    The table is matched on its **quoted** name rather than as a bare
    substring, so a future `accounts_organization_…` table can't satisfy
    it by accident (D27's trap). The quoted form is verified to match the
    real query by `test_creating_a_state_does_not_take_the_lock`'s
    counterpart assertions — every other test here would go red if the
    matcher stopped matching, rather than quietly passing."""

    def setUp(self):
        self.org, self.admin = make_admin_org("Mechanism", "admin@example.com")
        self.client.force_login(self.admin)

    @staticmethod
    def _lock_and_first_read(queries):
        """Index of the organization row lock, and of the first read of the
        workflow-state table. Either may be None."""
        lock_at = first_read_at = None
        for i, q in enumerate(queries.captured_queries):
            sql = q["sql"].upper()
            if lock_at is None and "FOR UPDATE" in sql and '"ACCOUNTS_ORGANIZATION"' in sql:
                lock_at = i
            if first_read_at is None and '"ACTIVITIES_WORKFLOWSTATE"' in sql and sql.startswith(
                "SELECT"
            ):
                first_read_at = i
        return lock_at, first_read_at

    def test_the_delete_path_locks_the_organization_row_before_reading(self):
        alpha, _beta = _two_plain_states(self.org)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.delete(f"/api/workflow-states/{alpha.id}/")
        self.assertEqual(response.status_code, 204)

        lock_at, first_read_at = self._lock_and_first_read(queries)
        self.assertIsNotNone(
            lock_at,
            "deleting a workflow state must lock the organization row; no "
            "SELECT ... FOR UPDATE on accounts_organization was issued",
        )
        self.assertIsNotNone(first_read_at, "the guard reads no workflow state at all")
        self.assertLess(
            lock_at,
            first_read_at,
            "the lock must be taken before the guard reads, or it serialises "
            "nothing — the response is identical either way",
        )

    def test_the_update_path_locks_the_organization_row_before_reading(self):
        done, _closed = _two_done_states(self.org)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.patch(
                f"/api/workflow-states/{done.id}/",
                data=json.dumps({"is_done": False}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)

        lock_at, first_read_at = self._lock_and_first_read(queries)
        self.assertIsNotNone(
            lock_at, "editing a workflow state must lock the organization row"
        )
        self.assertIsNotNone(first_read_at, "the guard reads no workflow state at all")
        self.assertLess(lock_at, first_read_at, "the lock must be taken before the guard reads")

    def test_creating_a_state_does_not_take_the_lock(self):
        """A write that can only *raise* the protected counts shouldn't
        contend for the lock — stated in apps/accounts/locking.py, pinned
        here so a later "be consistent" pass goes red rather than quietly
        serialising every write in the org."""
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(
                "/api/workflow-states/",
                data=json.dumps({"name": "Blocked", "order": 9}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 201)
        lock_at, _ = self._lock_and_first_read(queries)
        self.assertIsNone(lock_at, "creating a workflow state should not lock the org row")


class WorkflowStateGuardsStillWorkTests(TestCase):
    """These pass both before and after the fix, deliberately. A lock is a
    good way to break an endpoint, and the ordinary paths have to keep
    working — the D10 precedent, where a change to a lockout guard made it
    fire on something it was never meant to protect."""

    def setUp(self):
        self.org, self.admin = make_admin_org("Sequential", "admin@example.com")
        self.client.force_login(self.admin)

    def test_the_last_state_still_cannot_be_deleted(self):
        alpha, beta = _two_plain_states(self.org)
        self.assertEqual(self.client.delete(f"/api/workflow-states/{alpha.id}/").status_code, 204)

        response = self.client.delete(f"/api/workflow-states/{beta.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("at least one workflow state", response.json()["detail"])

    def test_the_only_done_state_still_cannot_be_un_flagged(self):
        done, closed = _two_done_states(self.org)
        self.assertEqual(
            self.client.patch(
                f"/api/workflow-states/{closed.id}/",
                data=json.dumps({"is_done": False}),
                content_type="application/json",
            ).status_code,
            200,
        )

        response = self.client.patch(
            f"/api/workflow-states/{done.id}/",
            data=json.dumps({"is_done": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("only state marked as finished", str(response.json()))

    def test_an_ordinary_rename_still_saves(self):
        alpha, _beta = _two_plain_states(self.org)
        response = self.client.patch(
            f"/api/workflow-states/{alpha.id}/",
            data=json.dumps({"name": "Renamed"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        alpha.refresh_from_db()
        self.assertEqual(alpha.name, "Renamed")

    def test_another_organizations_state_is_still_out_of_reach(self):
        """The lock is taken on the *caller's* org, so a cross-org id must
        still 404 rather than locking someone else's row on the way to
        finding out."""
        other, _other_admin = make_admin_org("Elsewhere", "elsewhere@example.com")
        theirs, _ = _two_plain_states(other)

        self.assertEqual(self.client.delete(f"/api/workflow-states/{theirs.id}/").status_code, 404)
        self.assertEqual(
            self.client.patch(
                f"/api/workflow-states/{theirs.id}/",
                data=json.dumps({"name": "Mine now"}),
                content_type="application/json",
            ).status_code,
            404,
        )
        theirs.refresh_from_db()
        self.assertEqual(theirs.name, "Alpha")
