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

from django.contrib.gis.geos import Polygon
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, TransactionTestCase

from apps.accounts.models import Membership, Organization, Property, User
from apps.activities.models import Activity, ActivitySpecies
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
