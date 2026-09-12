"""Regression tests for apps.species.

**Deleting a species that's in use is a refusal, not a crash** (D13, found
and fixed 2026-09-08) — this repo's bar for a checked-in test being "this
already regressed silently once".

Both FKs into `Species` are `PROTECT` — `Sighting.species` and
`ActivitySpecies.species` — so deleting a referenced species raises
`ProtectedError`. Nothing converted it: it subclasses `IntegrityError`, not
`APIException`, DRF's `exception_handler` returns `None` for it, and there
is no custom `EXCEPTION_HANDLER`. It therefore reached the user as a **500**
from the ordinary Delete button on the species page.

What makes this worth a test rather than a shrug: **the same pattern was
already fixed twice, in one file, with comments saying so.**
`WorkflowStateViewSet.destroy` and `ActivityTypeViewSet.destroy` each guard
their own `PROTECT` FK and return a 400 naming how many records are in the
way. Species is the third per-org reference list and was the only one
without the guard.

Two things here are more than a restatement of the fix:

- `test_two_links_to_one_activity_count_as_one_activity` pins a nuance the
  obvious implementation gets wrong. `ActivitySpecies` has **no** unique
  constraint on `(activity, species)` — only the POST path's `get_or_create`
  keeps it to one row per pair — so counting through-rows would overstate
  how many activities an admin actually has to go and fix.
- `test_an_unused_species_is_still_deletable` is the guard against a "fix"
  that simply refuses every delete.

Run with: python manage.py test apps.species
"""

from django.contrib.gis.geos import Point, Polygon
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Membership, Organization, Property, User
from apps.activities.models import Activity, ActivitySpecies
from apps.sightings.models import Sighting
from apps.species.models import Species


class DeletingAnInUseSpeciesIsRefusedNotCrashedTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="admin@example.com", password="pw-12345678"
        )
        # Delete is admin-gated by OrganizationScopedViewSet.
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Test Property",
            boundary=Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
        )
        self.species = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )
        self.client.force_login(self.user)

    def url(self, species=None):
        return f"/api/species/{(species or self.species).id}/"

    def add_sighting(self):
        return Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=self.species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
        )

    def add_activity(self):
        activity = Activity.objects.create(
            organization=self.org,
            property=self.property,
            activity_type=self.org.activity_types.first(),
            status=self.org.workflow_states.first(),
            geometry=Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
        )
        ActivitySpecies.objects.create(activity=activity, species=self.species)
        return activity

    # --- The defect: a 400, not a 500 ---

    def test_a_species_used_by_a_sighting_cannot_be_deleted(self):
        self.add_sighting()
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Species.objects.filter(id=self.species.id).exists())

    def test_a_species_used_by_an_activity_cannot_be_deleted(self):
        self.add_activity()
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Species.objects.filter(id=self.species.id).exists())

    # --- The message names both relations ---

    def test_the_message_names_sightings(self):
        self.add_sighting()
        detail = self.client.delete(self.url()).json()["detail"]
        self.assertIn("1 sighting", detail)
        self.assertIn("uses", detail)

    def test_the_message_names_activities(self):
        self.add_activity()
        detail = self.client.delete(self.url()).json()["detail"]
        self.assertIn("1 activity", detail)

    def test_the_message_names_both_when_both_are_in_the_way(self):
        """The reason this guard isn't a copy of its two siblings: an admin
        told only "2 records" has to hunt across two different pages."""
        self.add_sighting()
        self.add_activity()
        detail = self.client.delete(self.url()).json()["detail"]
        self.assertIn("1 sighting", detail)
        self.assertIn("1 activity", detail)
        self.assertIn("use", detail)

    def test_plurals_read_correctly(self):
        self.add_sighting()
        self.add_sighting()
        self.add_activity()
        self.add_activity()
        detail = self.client.delete(self.url()).json()["detail"]
        self.assertIn("2 sightings", detail)
        self.assertIn("2 activities", detail)
        self.assertIn("still use this species", detail)

    def test_one_activity_cannot_hold_the_same_species_twice(self):
        """This test used to *construct* the duplicate state on purpose:
        ActivitySpecies had no unique constraint on (activity, species), so
        counting through-rows instead of distinct activities would have told
        an admin to go and fix two activities that don't exist.

        D18 (2026-09-10) put the constraint there, so that state is no
        longer reachable — the fixture this test was built on is now
        refused by the database. Rather than delete the test, it asserts the
        stronger fact from the species side: the duplicate can't be made,
        and the message still says one activity. `test_plurals_read_correctly`
        above covers counting across genuinely distinct activities."""
        activity = self.add_activity()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ActivitySpecies.objects.create(activity=activity, species=self.species)

        detail = self.client.delete(self.url()).json()["detail"]
        self.assertIn("1 activity", detail)
        self.assertNotIn("2 activities", detail)

    # --- Guard against a fix that refuses everything ---

    def test_an_unused_species_is_still_deletable(self):
        response = self.client.delete(self.url())
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Species.objects.filter(id=self.species.id).exists())

    def test_deleting_one_species_is_unaffected_by_another_being_in_use(self):
        self.add_sighting()
        spare = Species.objects.create(organization=self.org, common_name="Spare")
        response = self.client.delete(self.url(spare))
        self.assertEqual(response.status_code, 204)

    def test_a_species_becomes_deletable_once_its_last_user_goes(self):
        """The refusal is a real state an admin can get out of, not a
        permanent block."""
        sighting = self.add_sighting()
        self.assertEqual(self.client.delete(self.url()).status_code, 400)
        sighting.delete()
        self.assertEqual(self.client.delete(self.url()).status_code, 204)


class AddingADuplicateSpeciesIsRefusedNotCrashedTests(TestCase):
    """**Adding a species you already have was a 500** (D26, found and fixed
    2026-09-12), reachable from the ordinary Add form on the species page by
    typing a name twice.

    `Species.Meta` carries `UniqueConstraint(["organization",
    "common_name"])`, but `organization` is supplied by the viewset rather
    than the request body, so DRF never builds its auto-generated
    unique-together validator and nothing converted the resulting
    `IntegrityError` — same shape as D13 one class above, and the same
    reason it surfaced as a 500 rather than a message.

    Found while building D24 (quick log's inline "add a new species"),
    which routes a **second** caller into this path — from a mobile capture
    flow with no draft persistence, where a 500 costs the user the point
    they just placed.

    The tests split the way D22's did, because the defect and its most
    attractive wrong fix need different tests:

    - The **outcome** tests pin the 400. They pass against either a
      validator-only fix or the shipped two-layer one.
    - `test_a_differently_cased_name_is_still_accepted` is the
      **constraint** test, and it is the one doing real work. The tempting
      fix is to mirror the two sibling guards
      (`WorkflowStateSerializer`/`ActivityTypeSerializer`) and match
      `__iexact` — which would *also* start rejecting "crabgrass" beside
      "Crabgrass", quietly settling an owner question this queue has
      deliberately left open since 2026-09-10 ("needs a `Lower()`
      constraint **and** a decision about existing rows — a product call").
      Every outcome test passes against that fix. Only this one fails.
    - `test_the_view_converts_an_integrity_error_rather_than_500ing` is the
      **mechanism** test. Validation and the database are not the same
      guard: between the check and the write sits a real window (a stale
      client list, two tabs, two members). A validator-only fix leaves that
      window a 500 and passes every other test here.

    Run with: python manage.py test apps.species
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Dup Org")
        self.user = User.objects.create_user(email="dup@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.EDITOR
        )
        self.client.force_login(self.user)
        self.existing = Species.objects.create(organization=self.org, common_name="Crabgrass")

    def post(self, name):
        return self.client.post("/api/species/", {"common_name": name}, content_type="application/json")

    # --- Outcome: a refusal, not a crash ---

    def test_a_duplicate_name_is_refused_with_400(self):
        response = self.post("Crabgrass")
        self.assertEqual(
            response.status_code,
            400,
            "adding a species you already have must be a refusal, not a 500",
        )
        self.assertIn("common_name", response.json())

    def test_the_duplicate_is_not_created(self):
        self.post("Crabgrass")
        self.assertEqual(Species.objects.filter(organization=self.org, common_name="Crabgrass").count(), 1)

    def test_surrounding_whitespace_does_not_smuggle_a_duplicate_past(self):
        """The name is stripped before storage, so "  Crabgrass  " would
        otherwise be stored as a second row reading identically."""
        self.assertEqual(self.post("   Crabgrass   ").status_code, 400)

    def test_renaming_onto_an_existing_name_is_refused(self):
        other = Species.objects.create(organization=self.org, common_name="Milkweed")
        response = self.client.patch(
            f"/api/species/{other.id}/",
            {"common_name": "Crabgrass"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    # --- Constraint: this must NOT quietly answer the open casing question ---

    def test_a_differently_cased_name_is_still_accepted(self):
        """**The test that catches the attractive wrong fix.**

        Mirroring the sibling guards' `__iexact` would reject this. That is
        a product decision the owner has not made — it needs a `Lower()`
        functional constraint and a call about existing differently-cased
        rows — and a 500 fix is not the place to make it. The database
        accepts this today; after the fix it must still accept it.
        """
        response = self.post("crabgrass")
        self.assertEqual(
            response.status_code,
            201,
            "case-sensitivity is an open owner question — the duplicate "
            "guard must not settle it as a side effect",
        )

    # --- Mechanism: the database is the enforcement, not the validator ---

    def test_the_view_converts_an_integrity_error_rather_than_500ing(self):
        """Forces the race window open by neutralising the validator, so
        the `IntegrityError` handler in `SpeciesViewSet.perform_create` is
        the only guard left. A validator-only fix fails here and passes
        everything else.
        """
        from unittest.mock import patch

        from apps.species.serializers import SpeciesSerializer

        with patch.object(SpeciesSerializer, "validate_common_name", lambda self, value: value.strip()):
            response = self.post("Crabgrass")
        self.assertEqual(
            response.status_code,
            400,
            "the constraint must be converted to a refusal even when the "
            "validator didn't catch it first — that window is real",
        )

    # --- Guards against a fix that refuses too much ---

    def test_a_genuinely_new_name_is_still_created(self):
        response = self.post("Big Bluestem")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Species.objects.filter(organization=self.org, common_name="Big Bluestem").exists())

    def test_renaming_a_species_to_its_own_name_still_works(self):
        """The clash check must exclude the instance being edited, or
        saving an unrelated field on the form would refuse itself."""
        response = self.client.patch(
            f"/api/species/{self.existing.id}/",
            {"common_name": "Crabgrass", "scientific_name": "Digitaria"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

    def test_another_organization_may_still_use_the_same_name(self):
        """Uniqueness is per-organization. A guard that forgot the org
        filter would make one org's list constrain another's."""
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(email="other@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=other_org, user=other_user, role=Membership.Role.EDITOR
        )
        self.client.force_login(other_user)
        self.assertEqual(self.post("Crabgrass").status_code, 201)
