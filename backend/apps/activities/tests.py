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

from django.contrib.gis.geos import Polygon
from django.test import TestCase

from apps.accounts.models import Membership, Organization, Property, User
from apps.activities.models import Activity, ActivitySpecies
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
