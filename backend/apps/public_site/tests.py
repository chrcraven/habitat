"""Regression tests for the public site's visibility rules.

These exist because of a specific defect (2026-09-04): soft delete shipped
on 2026-08-29 and covered the authenticated app carefully — including its
function-based photo views — but `apps/public_site/` was never opened, so
deleting a property left its already-published photos serving to anonymous
visitors for the whole 30-day retention window. The inversion is the
clearest statement of it: flipping a property *private* cut those photos
off, while *deleting* it did not — the stronger action retracted less.

The root cause is one Django semantic that is easy to lose and impossible
to see in a diff: `property__is_public=True` is a plain SQL join and does
**not** consult `Property.objects`' soft-delete filter, and a soft-deleted
property keeps `is_public=True`. So every public query that reaches a
Property through a join needs `property__deleted_at__isnull=True` spelled
out. `test_prefix_filter_still_matches_a_deleted_property` below pins that
semantic directly, so if a future Django version ever changes it, this
tells you *why* the other assertions matter rather than just failing.

Run with: python manage.py test apps.public_site
"""

from django.contrib.gis.geos import Point, Polygon
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Organization, Property
from apps.activities.models import Activity, ActivityPhoto, ActivityType, WorkflowState
from apps.sightings.models import Sighting, SightingActivityLink, SightingPhoto
from apps.species.models import Species

SQUARE = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))


class PublicSiteSoftDeleteTests(TestCase):
    """A soft-deleted property must retract everything it had published,
    and get it all back on restore."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        # WorkflowState/ActivityType rows are seeded per-org by a post_save
        # signal (see apps/activities/models.py) — reuse them rather than
        # creating duplicates that would trip their uniqueness constraints.
        self.status = WorkflowState.objects.filter(organization=self.org).first()
        self.activity_type = ActivityType.objects.filter(organization=self.org).first()
        self.species = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )
        self.live = self._make_property("Live Property")
        self.doomed = self._make_property("Doomed Property")
        self.live_activity, self.live_sighting = self._make_records(self.live)
        self.doomed_activity, self.doomed_sighting = self._make_records(self.doomed)
        # Links are deliberately NOT constrained to a single property (see
        # SightingActivityLinkSerializer, which even serves
        # activity_property_name), so a live property's activity can point
        # at a sighting on a property that later gets deleted.
        SightingActivityLink.objects.create(
            activity=self.live_activity, sighting=self.doomed_sighting
        )

    def _make_property(self, name):
        return Property.objects.create(
            organization=self.org, name=name, boundary=SQUARE, is_public=True
        )

    def _make_records(self, property_):
        activity = Activity.objects.create(
            organization=self.org,
            property=property_,
            activity_type=self.activity_type,
            status=self.status,
            geometry=SQUARE,
            is_public=True,
        )
        ActivityPhoto.objects.create(
            activity=activity, image=b"\x89PNG-activity", content_type="image/png"
        )
        sighting = Sighting.objects.create(
            organization=self.org,
            property=property_,
            species=self.species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
        )
        SightingPhoto.objects.create(
            sighting=sighting, image=b"\x89PNG-sighting", content_type="image/png"
        )
        return activity, sighting

    # -- URLs under test ---------------------------------------------------

    def _doomed_urls(self):
        activity_photo = self.doomed_activity.photos.first()
        sighting_photo = self.doomed_sighting.photos.first()
        return {
            "activity photo list": f"/api/public/activities/{self.doomed_activity.id}/photos/",
            "activity photo image": (
                f"/api/public/activities/{self.doomed_activity.id}"
                f"/photos/{activity_photo.id}/image/"
            ),
            "sighting photo list": f"/api/public/sightings/{self.doomed_sighting.id}/photos/",
            "sighting photo image": (
                f"/api/public/sightings/{self.doomed_sighting.id}"
                f"/photos/{sighting_photo.id}/image/"
            ),
            "property page": f"/api/public/properties/{self.doomed.id}/",
        }

    def _live_urls(self):
        return {
            "activity photo list": f"/api/public/activities/{self.live_activity.id}/photos/",
            "property page": f"/api/public/properties/{self.live.id}/",
        }

    def _linked_sighting_ids(self):
        """The sighting ids the public API attaches to the LIVE property's
        activity — which include a sighting on the doomed property."""
        body = self.client.get(
            f"/api/public/properties/{self.live.id}/activities/"
        ).json()
        for feature in body["features"]:
            if feature["id"] == self.live_activity.id:
                return feature["properties"]["linked_sighting_ids"]
        return None

    def _soft_delete(self, property_):
        property_.deleted_at = timezone.now()
        property_.save(update_fields=["deleted_at"])

    # -- Tests -------------------------------------------------------------

    def test_published_photos_serve_while_the_property_is_live(self):
        for label, url in {**self._doomed_urls(), **self._live_urls()}.items():
            with self.subTest(url=label):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_soft_delete_retracts_published_photos(self):
        """The defect itself: before the fix these all returned 200."""
        self._soft_delete(self.doomed)
        for label, url in self._doomed_urls().items():
            with self.subTest(url=label):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_soft_delete_does_not_affect_other_properties(self):
        self._soft_delete(self.doomed)
        for label, url in self._live_urls().items():
            with self.subTest(url=label):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_soft_delete_retracts_ids_from_a_cross_property_link_list(self):
        """A link may span properties, so a live activity's link list can
        name a sighting on the deleted property — it must stop doing so."""
        self.assertEqual(self._linked_sighting_ids(), [self.doomed_sighting.id])
        self._soft_delete(self.doomed)
        self.assertEqual(self._linked_sighting_ids(), [])

    def test_restore_republishes_everything(self):
        """`deleted_at` is simply cleared, so nothing needs re-publishing
        by hand — the same filters that hid it stop matching."""
        self._soft_delete(self.doomed)
        self.doomed.deleted_at = None
        self.doomed.save(update_fields=["deleted_at"])
        for label, url in self._doomed_urls().items():
            with self.subTest(url=label):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(self._linked_sighting_ids(), [self.doomed_sighting.id])

    def test_marking_a_property_private_still_retracts_photos(self):
        """The behavior that already worked, and against which deletion
        was the anomaly — pinned so a future change can't invert it back."""
        self.doomed.is_public = False
        self.doomed.save(update_fields=["is_public"])
        for label, url in self._doomed_urls().items():
            with self.subTest(url=label):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_prefix_filter_still_matches_a_deleted_property(self):
        """Pins the Django semantic the whole defect rested on: a related
        -field filter is a join and ignores the related model's default
        manager, so `is_public` alone is NOT enough."""
        self._soft_delete(self.doomed)
        self.assertTrue(
            Activity.objects.filter(
                id=self.doomed_activity.id, is_public=True, property__is_public=True
            ).exists(),
            "A join-only filter should still match; if this ever fails, the "
            "explicit deleted_at guards below may have become redundant.",
        )
        self.assertFalse(
            Activity.objects.filter(
                id=self.doomed_activity.id,
                is_public=True,
                property__is_public=True,
                property__deleted_at__isnull=True,
            ).exists()
        )
