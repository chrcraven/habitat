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

    def test_two_links_to_one_activity_count_as_one_activity(self):
        """ActivitySpecies has no unique constraint on (activity, species) —
        only the POST path's get_or_create keeps it to one row per pair — so
        counting through-rows instead of distinct activities would tell an
        admin to go and fix two activities that don't exist."""
        activity = self.add_activity()
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
