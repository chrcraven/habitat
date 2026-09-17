"""Regression tests for apps.accounts. Eleven unrelated defects are pinned
here, each in its own section; all are "this already regressed silently
once", which is this repo's bar for a checked-in test.

(The list below stops at 7 because it was written when the file did.
Sections 8-11 introduce themselves where they sit: D27 list queries, D33
image revalidation, D38 attribution, and D40 rate limiting.)

1. **Images** (D6, 2026-09-06) — what Habitat accepts as an image, and what
   it serves that image back as. Immediately below.
2. **Signup does not publish the user's email address** (D8, 2026-09-07) —
   see SignupDoesNotPublishTheEmailTests further down.
3. **Deleting a property does not widen anyone's access** (D10,
   2026-09-07) — see PropertyScopeSurvivesSoftDeleteTests further down.
4. **A malformed integer query parameter is refused, not a 500** (D14,
   2026-09-08) — see MalformedIntegerQueryParamsTests further down. It
   lives here rather than in one of the four apps whose endpoints it
   covers, because the shared helper it exercises
   (apps/accounts/query_params.py) does.
5. **The last-account-wide-admin guard can't be raced** (D16, 2026-09-09) —
   see LastAdminGuardConcurrencyTests further down. The only genuinely
   concurrent tests in the suite: they need real threads and real committed
   transactions, so they are a TransactionTestCase.
6. **A QR center image can't exhaust the server** (D17, 2026-09-10) — see
   QrLogoIsBoundedTests further down.
7. **The "forgot password" answer is one answer** (D22, 2026-09-11) — see
   PasswordResetRequestGivesOneAnswerTests at the bottom. It pins the
   anti-enumeration property that constrains how that message may be
   worded, rather than the wording itself.

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

import io
import re
import json
import threading
import time
from unittest import mock

from django.contrib.gis.geos import Point, Polygon
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.conf import settings
from django.test import (
    Client,
    SimpleTestCase,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.accounts.images import (
    ALLOWED_IMAGE_TYPES,
    FALLBACK_CONTENT_TYPE,
    UNSUPPORTED_TYPE_MESSAGE,
    image_content_type,
    normalize_image_type,
    validate_image_upload,
)
from apps.accounts import throttling, views
from apps.accounts.models import (
    Invitation,
    Membership,
    Organization,
    PasswordResetToken,
    Property,
    User,
)
from apps.accounts.org_scoping import (
    ensure_account_wide_admin,
    filter_by_property_scope,
    get_active_membership,
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


# --- 6. A QR center image can't exhaust the server (D17, 2026-09-10) ---
#
# `_qr_response` read an uploaded `logo` straight into memory and handed the
# bytes to Pillow with no size check, no type check and no pixel check. It
# was the only one of the app's five image inputs with none of the three,
# and the only one with no role gate, so a *viewer* could reach it.
#
# The measurement that makes it a defect rather than a nit: a flat-colour
# 9000x9000 PNG is a ~250KB file — unremarkable in any log, under any edge
# proxy's body limit — that cost ~300MB of resident memory and ~2.7s of CPU
# to decode, and returned 200. Pillow's own DecompressionBomb guard did not
# help: it only engages above 89,478,485 pixels, so an attacker simply stays
# beneath it. Nothing warned and nothing raised.
#
# Two things are pinned here, and the second is the one an outcome-only test
# would miss:
#
# 1. **The oversized cases are refused.** Straightforward.
# 2. **They are refused *before* the work happens.** A "fix" that decoded
#    first and measured afterwards would return the same 400 and pass every
#    assertion in (1) while fixing nothing at all — the memory would still
#    have been spent. `test_an_oversized_image_is_never_decoded` asserts the
#    decode is never reached, and the two ordering tests prove the byte and
#    type checks precede the read by sending bodies whose *content* would
#    produce a different message if it had been looked at.


def _png_bytes(width, height):
    """A large-dimension but small-on-disk PNG. Flat colour compresses hard,
    which is precisely the asymmetry D17 turns on: the byte count says
    nothing about what decoding it will cost."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (0, 128, 64)).save(
        buffer, format="PNG", compress_level=9
    )
    return buffer.getvalue()


class QrLogoIsBoundedTests(TestCase):
    """The refusals. Each of these fails against the pre-fix code."""

    def setUp(self):
        self.organization = Organization.objects.create(name="QR Org")
        self.user = _make_account_wide_admin(self.organization, "qr@example.com")
        self.client.force_login(self.user)

    def _post(self, logo=None):
        data = {"base_url": "https://public.example.com"}
        if logo is not None:
            data["logo"] = logo
        return self.client.post("/api/org/qr/", data)

    def test_an_image_over_the_pixel_cap_is_refused(self):
        """The D17 case itself: 81 megapixels from a ~250KB upload."""
        logo = SimpleUploadedFile(
            "bomb.png", _png_bytes(9000, 9000), content_type="image/png"
        )
        response = self._post(logo)

        self.assertEqual(response.status_code, 400)
        self.assertIn("dimensions are too large", response.json()["detail"])

    def test_an_oversized_image_is_never_decoded(self):
        """The mechanism, and the reason this section isn't outcome-only.

        A guard that decoded first and checked `.size` afterwards would
        return the identical 400 above while spending the identical memory.
        `Image.open()` is lazy — it parses the header and exposes `.size`
        without decoding — and `.convert()` is what forces the decode, so
        asserting `.convert()` is never reached asserts the guard runs in
        the order that makes it worth anything."""
        from PIL import Image

        calls = []
        original = Image.Image.convert

        def spy(self, *args, **kwargs):
            calls.append(self.size)
            return original(self, *args, **kwargs)

        logo = SimpleUploadedFile(
            "bomb.png", _png_bytes(9000, 9000), content_type="image/png"
        )
        with mock.patch.object(Image.Image, "convert", spy):
            response = self._post(logo)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn(
            (9000, 9000),
            calls,
            "the oversized logo was decoded before being rejected — the "
            "guard ran after the work it exists to prevent",
        )

    def test_an_image_over_the_byte_cap_is_refused_without_being_read(self):
        """Ordering, proved without patching anything.

        The body is 6MB of bytes that are not an image at all. If the view
        read and decoded it before checking the size, Pillow would fail and
        the message would be "Could not read the center image." Getting the
        *size* message instead is what proves the byte check came first."""
        logo = SimpleUploadedFile(
            "big.png", b"A" * (6 * 1024 * 1024), content_type="image/png"
        )
        response = self._post(logo)

        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertIn("too large", detail)
        self.assertNotIn("Could not read", detail)

    def test_a_scriptable_type_is_refused_with_the_format_message(self):
        """Same ordering argument, for the type check. The bytes are a
        perfectly valid PNG, so a decode would succeed and return 200; only
        the declared type is wrong. A format message here proves the
        allowlist ran, and is also what makes the manual's claim that "the
        picker only offers the accepted formats" true of this endpoint."""
        logo = SimpleUploadedFile(
            "logo.svg", _png_bytes(64, 64), content_type="image/svg+xml"
        )
        response = self._post(logo)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], UNSUPPORTED_TYPE_MESSAGE)

    def test_the_pixel_cap_boundary_is_exact(self):
        """Patches the constant rather than decoding a real 16MP image, so
        the boundary is pinned precisely and the suite stays quick."""
        from apps.accounts import qrcodes

        with mock.patch.object(qrcodes, "MAX_LOGO_PIXELS", 40 * 40):
            allowed = self._post(
                SimpleUploadedFile(
                    "ok.png", _png_bytes(40, 40), content_type="image/png"
                )
            )
            refused = self._post(
                SimpleUploadedFile(
                    "no.png", _png_bytes(41, 40), content_type="image/png"
                )
            )

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(refused.status_code, 400)


class QrCodeStillWorksTests(TestCase):
    """These pass both before and after the fix, deliberately.

    Every assertion above is a refusal, and the cheapest way to make all of
    them pass is to break the endpoint outright. These pin the job it is
    actually for, so that "fix" goes red."""

    def setUp(self):
        self.organization = Organization.objects.create(name="QR Org")
        self.user = _make_account_wide_admin(self.organization, "qr@example.com")
        self.client.force_login(self.user)

    def _post(self, **extra):
        return self.client.post(
            "/api/org/qr/", {"base_url": "https://public.example.com", **extra}
        )

    def test_a_code_with_no_logo_is_still_generated(self):
        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG"))

    def test_an_ordinary_logo_is_still_accepted(self):
        logo = SimpleUploadedFile(
            "logo.png", _png_bytes(512, 512), content_type="image/png"
        )
        response = self._post(logo=logo)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_a_viewer_can_still_generate_a_code(self):
        """Pinned because "add a role gate" is a tempting way to answer a
        resource-exhaustion finding, and it would be a silent product
        change. The endpoint is deliberately open to any member — it exposes
        nothing that isn't already on the public site (see the comment above
        _qr_response). D17 is fixed by bounding the resource, not by
        narrowing who may ask for it."""
        viewer_user = User.objects.create_user(
            email="viewer@example.com", password="pw-for-testing-123"
        )
        Membership.objects.create(
            user=viewer_user,
            organization=self.organization,
            role=Membership.Role.VIEWER,
        )
        self.client.force_login(viewer_user)

        response = self._post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")


class QrLogoLimitsAreDocumentedTests(SimpleTestCase):
    """The constants are the whole fix, so their values are asserted rather
    than left implicit. A later session tightening MAX_LOGO_PIXELS to
    something that refuses a real logo, or loosening it back above Pillow's
    own threshold (where it would stop being the guard that fires), should
    have to change a test that says why."""

    def test_the_pixel_cap_admits_a_full_resolution_phone_photo(self):
        from apps.accounts.qrcodes import MAX_LOGO_PIXELS

        self.assertGreaterEqual(MAX_LOGO_PIXELS, 12_000_000)

    def test_the_pixel_cap_is_well_below_pillows_own_threshold(self):
        """Pillow's guard only engages above MAX_IMAGE_PIXELS. If ours ever
        rose above that, the gap beneath it — which is the entire finding —
        would reopen."""
        from PIL import Image

        from apps.accounts.qrcodes import MAX_LOGO_PIXELS

        self.assertLess(MAX_LOGO_PIXELS, Image.MAX_IMAGE_PIXELS)

    def test_the_byte_cap_matches_the_theme_banner_cap(self):
        from apps.accounts.qrcodes import MAX_LOGO_BYTES
        from apps.accounts.theming import MAX_THEME_IMAGE_BYTES

        self.assertEqual(MAX_LOGO_BYTES, MAX_THEME_IMAGE_BYTES)


# --- 7. The "forgot password" answer is one answer (D22, 2026-09-11) ---
#
# This section pins the property that constrains how that message may be
# worded, not the wording itself — a test asserting the literal string would
# just have to be edited alongside every future copy change, which teaches a
# reader nothing and catches nothing.
#
# The defect (D22, found 2026-09-11 by a check-in, this half fixed the same
# day): the endpoint answered "…a reset link has been sent." That is a flat
# assertion of an accomplished fact the server never verified. EMAIL_BACKEND
# defaults to Django's console backend, and send_password_reset_email is
# best-effort — it catches and logs its own exceptions — so a delivered
# message, a silently-failed SMTP connection and a line written to a log file
# all produce the identical 200 and the identical sentence. The flow also has
# no "copy the link" fallback (handing the link back would answer the
# question the generic response exists to refuse), no admin-side reset, and
# /forgot-password renders outside AppShell, so the reader cannot even reach
# the Help link that documents the caveat. A dead end presented as success,
# shown to the one person already locked out.
#
# The wording was the fixable half. Whether a locked-out user gets a real way
# out — an `email_configured` flag on the config endpoint, or an admin-side
# reset action — is the owner's call and deliberately stays open, so these
# tests assert nothing about it.


class PasswordResetRequestGivesOneAnswerTests(TestCase):
    """The response must not vary with whether the email has an account.

    That is the anti-enumeration stance the whole flow is built around, and
    it is the reason this message is hard to word well: every "friendlier"
    rewrite that tells the user something *useful* about their own address
    ("we couldn't find that account", "check your inbox") breaks it. Pinning
    it here means a future edit that reintroduces a branch goes red instead
    of quietly turning the form into an oracle.
    """

    URL = "/api/auth/password-reset/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="real@example.com", password="Sufficiently-Long-Pw-1"
        )

    def test_a_real_and_an_unknown_address_get_identical_responses(self):
        known = self.client.post(
            self.URL, {"email": "real@example.com"}, content_type="application/json"
        )
        unknown = self.client.post(
            self.URL, {"email": "nobody@example.com"}, content_type="application/json"
        )

        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(
            known.json(),
            unknown.json(),
            "the reset response must not differ between a registered and an "
            "unregistered address — that difference is a user-enumeration oracle",
        )

    def test_the_identical_answer_is_not_achieved_by_doing_nothing(self):
        """The pairing that makes the test above mean something.

        Two endpoints that both no-op would also return identical responses
        and satisfy it. This asserts the real work still happens behind the
        generic answer: a token is minted for the address that has an
        account, and not for the one that doesn't.
        """
        self.client.post(
            self.URL, {"email": "real@example.com"}, content_type="application/json"
        )
        self.assertEqual(PasswordResetToken.objects.filter(user=self.user).count(), 1)

        self.client.post(
            self.URL, {"email": "nobody@example.com"}, content_type="application/json"
        )
        self.assertEqual(
            PasswordResetToken.objects.count(),
            1,
            "an unknown address must not mint a token",
        )

    def test_an_empty_address_is_answered_the_same_way_too(self):
        """`email` is read with a `or ""` fallback and only queried `if email`,
        so the empty string takes a third branch through the function. It must
        land on the same answer as the other two, not on an error that says the
        field was blank."""
        blank = self.client.post(self.URL, {"email": ""}, content_type="application/json")
        known = self.client.post(
            self.URL, {"email": "real@example.com"}, content_type="application/json"
        )

        self.assertEqual(blank.status_code, known.status_code)
        self.assertEqual(blank.json(), known.json())

    def test_the_message_does_not_state_delivery_as_accomplished_fact(self):
        """The mechanism test for this defect.

        The two tests above pass just as happily against the pre-fix string —
        "has been sent" is equally generic, equally unbranched. What was wrong
        with it was not *variation*, it was *certainty*: it reported an
        outcome the code cannot observe. So this asserts the one word that
        distinguishes a claim about the mail from a claim about the request.
        Deliberately narrow — it pins the verb, not the sentence, so copy can
        still be reworded freely around it.
        """
        detail = views.password_reset_requested_detail().lower()

        self.assertNotIn("has been sent", detail)
        self.assertIn("requested", detail)

    def test_the_contact_comes_from_the_deployment_not_the_request(self):
        """SUPPORT_CONTACT names the operator of *this* deployment.

        Two directions, because the variable could break either of the
        properties above. Setting it must change who the reader is told to
        write to (otherwise the setting is decorative), and it must not
        make the reply vary by caller (otherwise it re-opens the
        enumeration oracle the generic wording exists to close).
        """
        with self.settings(SUPPORT_CONTACT="ranger@example.org"):
            known = self.client.post(
                self.URL, {"email": "real@example.com"}, content_type="application/json"
            )
            unknown = self.client.post(
                self.URL, {"email": "nobody@example.com"}, content_type="application/json"
            )
            self.assertIn("ranger@example.org", known.json()["detail"])
            self.assertEqual(known.json(), unknown.json())

        with self.settings(SUPPORT_CONTACT=""):
            blank = self.client.post(
                self.URL, {"email": "real@example.com"}, content_type="application/json"
            )
        self.assertIn("whoever runs this", blank.json()["detail"].lower())
        self.assertNotIn("ranger@example.org", blank.json()["detail"])


# --- 8. List queries do not load image bytes (D27, 2026-09-13) ---
#
# Habitat stores images in the database, and every serializer in the app is
# careful never to put those bytes in a response — the two theme
# serializers emit a `has_theme_header_image` boolean, the two photo
# serializers emit a URL. All true, and all beside the point: a serializer
# decides what goes *out*, not what the queryset *loads*. Nothing deferred
# the blob columns, so every list query pulled them out of Postgres and
# threw them away.
#
# Measured on these very models before the fix: one property carrying a
# 5 MB banner, listed alongside 100 of its own sightings, produced **100
# distinct Python Property objects, each with its own copy of the bytes —
# a 524.7 MB peak**, against 0.4 MB with the blob deferred. Django does not
# dedupe a `select_related` target across rows, and the org-wide list pages
# are not paginated.
#
# Two things make this section's shape what it is:
#
# **The outcome is identical either way.** Every response below is
# byte-identical before and after the fix — that is what let this live for
# the life of the project. So the tests that do the real work here are
# *mechanism* tests (which columns the SQL selects, and how many queries a
# list costs), in the D16/D17/D18/D26 tradition.
#
# **The attractive wrong fix is `.only(...)`.** Listing the fields you want
# also defers the ones you forgot, and Django answers a touched deferred
# field with a fresh query per row. It returns the same JSON, so only
# `test_listing_many_properties_costs_a_constant_number_of_queries` and
# `test_the_content_type_column_is_still_loaded` can tell it apart. Built
# and measured: against `.only("id", "name", ...)` those two go red while
# every outcome test below stays green.
#
# **And the deferral must not cost data**, which is the one way this change
# could have been actively harmful rather than merely useless. Saving a
# model instance that has deferred fields is safe — Django narrows the
# UPDATE to the loaded columns — but "safe because of a Django internal"
# is exactly the kind of thing that should be pinned rather than trusted,
# because the failure mode is silent: renaming a property would blank its
# banner, and nothing else in the suite would notice.
#
# A measurement trap, recorded because it silently inverts a result:
# `"theme_header_image" in sql` is True *even when the blob is deferred*,
# because `theme_header_image_content_type` contains it as a substring. The
# helper below matches whole column names for that reason.

BANNER_BYTES = b"\x89PNG\r\n\x1a\n" + b"banner" * 64


def _theme_columns(queryset):
    """Whole column names, not a substring search — see the trap above."""
    return set(re.findall(r'"(theme_header_image\w*)"', str(queryset.query)))


class ListQueriesDoNotLoadImageBytesTests(TestCase):
    """Mechanism: the blob column is absent from the SQL a list issues, and
    the small column beside it is still present."""

    def setUp(self):
        self.org = Organization.objects.create(name="Blob Org")
        self.user = User.objects.create_user(email="blob@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Themed",
            boundary=SQUARE,
            is_public=True,
            theme_header_image=BANNER_BYTES,
            theme_header_image_content_type="image/png",
        )
        self.species = Species.objects.create(organization=self.org, common_name="Crabgrass")
        self.client.force_login(self.user)

    def _sighting(self):
        return Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=self.species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
        )

    def test_the_sighting_list_does_not_select_the_banner_blob(self):
        """The sharpest case: `select_related("property")` rebuilds the
        property per row, so this column was loaded once per sighting."""
        from apps.sightings.views import SightingViewSet

        columns = _theme_columns(SightingViewSet.queryset)

        self.assertNotIn(
            "theme_header_image",
            columns,
            "the sighting list still selects the banner bytes; with select_related "
            "they are loaded once per row",
        )

    def test_the_activity_list_does_not_select_the_banner_blob(self):
        from apps.activities.views import ActivityViewSet

        self.assertNotIn("theme_header_image", _theme_columns(ActivityViewSet.queryset))

    def test_the_property_list_does_not_select_the_banner_blob(self):
        from apps.accounts.views import PropertyViewSet

        self.assertNotIn("theme_header_image", _theme_columns(PropertyViewSet.queryset))

    def test_the_active_membership_query_does_not_select_the_banner_blob(self):
        """The hottest query in the app — `OrganizationRolePermission` and
        `OrganizationScopedViewSet` each run it, so an org banner would
        otherwise be loaded several times on every authenticated request."""
        membership = get_active_membership(self.user)

        self.assertIsNotNone(membership)
        self.assertIn(
            "theme_header_image",
            membership.organization.get_deferred_fields(),
            "the organization joined into every authenticated request still "
            "carries its banner bytes",
        )
        self.assertEqual(
            membership.organization.theme_header_image_content_type,
            "",
            "the content type beside it must stay loaded — it is what "
            "has_theme_header_image reads",
        )

    def test_the_content_type_column_is_still_loaded_everywhere(self):
        """The other half, and the one an `.only(...)` fix gets wrong:
        `has_theme_header_image` is derived from the content type, so that
        column must stay in every list query. Dropping it alongside the
        blob pushes it onto a per-row lookup while returning byte-identical
        JSON — which is why this is checked at *every* site rather than
        one. (Checked at one first; the naive fix sailed past it.)"""
        from apps.accounts.views import PropertyViewSet
        from apps.activities.views import ActivityViewSet
        from apps.sightings.views import SightingViewSet

        for label, qs in (
            ("properties", PropertyViewSet.queryset),
            ("activities", ActivityViewSet.queryset),
            ("sightings", SightingViewSet.queryset),
        ):
            with self.subTest(queryset=label):
                self.assertIn(
                    "theme_header_image_content_type",
                    _theme_columns(qs),
                    f"the {label} list no longer loads the content-type column — "
                    "has_theme_header_image will be answered per row",
                )

    def _list_properties_query_count(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/properties/")
        self.assertEqual(response.status_code, 200)
        return len(ctx.captured_queries), len(response.json()["features"])

    def test_listing_many_properties_costs_a_constant_number_of_queries(self):
        """The anti-`.only()` test, and the only one that catches it.

        Reading a field the queryset deferred costs one extra query *per
        row*, and the response body is byte-identical either way — so
        nothing but a query count can tell a correct deferral from an
        `.only(...)` that dropped a column the serializer reads.

        Counting *all* queries rather than grepping them for a column
        name is deliberate: the first version of this test filtered for
        the blob column specifically, and the naive fix's per-row lookups
        are for the *content type* beside it, so they went uncounted and
        the test passed against the very fix it exists to reject.
        """
        one_row, count = self._list_properties_query_count()
        self.assertEqual(count, 1)

        for i in range(12):
            Property.objects.create(
                organization=self.org,
                name=f"Extra {i}",
                boundary=SQUARE,
                theme_header_image=BANNER_BYTES,
                theme_header_image_content_type="image/png",
            )
        thirteen_rows, count = self._list_properties_query_count()
        self.assertEqual(count, 13)

        self.assertEqual(
            thirteen_rows,
            one_row,
            f"listing 13 properties took {thirteen_rows} queries where listing 1 took "
            f"{one_row} — the per-row growth means the serializer is reading a column "
            "the queryset deferred",
        )

    def test_the_sighting_list_loads_one_property_object_per_row_but_no_bytes(self):
        """States the actual defect: Django builds a separate Property per
        row and does not dedupe them, which is why the blob multiplied."""
        for _ in range(5):
            self._sighting()

        from apps.sightings.views import SightingViewSet

        rows = list(SightingViewSet.queryset.filter(organization=self.org))

        self.assertEqual(len(rows), 5)
        self.assertEqual(
            len({id(row.property) for row in rows}),
            5,
            "this test's premise is gone: Django now dedupes select_related targets, "
            "so the per-row blob duplication this section exists for cannot happen",
        )
        for row in rows:
            self.assertIn("theme_header_image", row.property.get_deferred_fields())


class DeferringTheBannerDoesNotLoseItTests(TestCase):
    """The one way this change could have been worse than the defect: if a
    save on a deferred instance wrote the blob column back as NULL, an
    ordinary rename would silently erase the banner."""

    def setUp(self):
        self.org = Organization.objects.create(name="Keep Org")
        self.user = User.objects.create_user(email="keep@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.org.theme_header_image = BANNER_BYTES
        self.org.theme_header_image_content_type = "image/png"
        self.org.save()
        self.property = Property.objects.create(
            organization=self.org,
            name="Before",
            boundary=SQUARE,
            is_public=True,
            theme_header_image=BANNER_BYTES,
            theme_header_image_content_type="image/png",
        )
        self.client.force_login(self.user)

    def test_renaming_a_property_keeps_its_banner(self):
        response = self.client.patch(
            f"/api/properties/{self.property.id}/",
            data=json.dumps({"properties": {"name": "After"}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        fresh = Property.all_objects.get(pk=self.property.pk)
        self.assertEqual(fresh.name, "After")
        self.assertEqual(
            bytes(fresh.theme_header_image),
            BANNER_BYTES,
            "renaming a property erased its header image — a save on an instance "
            "whose banner was deferred wrote the column back as NULL",
        )
        self.assertEqual(fresh.theme_header_image_content_type, "image/png")

    def test_renaming_the_organization_keeps_its_banner(self):
        response = self.client.patch(
            "/api/org/",
            data=json.dumps({"name": "Renamed"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        fresh = Organization.objects.get(pk=self.org.pk)
        self.assertEqual(fresh.name, "Renamed")
        self.assertEqual(bytes(fresh.theme_header_image), BANNER_BYTES)

    def test_soft_deleting_and_restoring_a_property_keeps_its_banner(self):
        self.assertEqual(
            self.client.delete(f"/api/properties/{self.property.id}/").status_code, 204
        )
        self.assertEqual(
            self.client.post(f"/api/properties/{self.property.id}/restore/").status_code, 200
        )

        fresh = Property.objects.get(pk=self.property.pk)
        self.assertIsNone(fresh.deleted_at)
        self.assertEqual(bytes(fresh.theme_header_image), BANNER_BYTES)


class ImagesAreStillServedAndReportedTests(TestCase):
    """Outcome: every response is byte-identical to before the deferral.
    These pass against the pre-fix code too, deliberately — they are what
    stops a future "fix" from deferring a column something actually reads.
    """

    def setUp(self):
        self.org = Organization.objects.create(name="Serve Org")
        self.user = User.objects.create_user(email="serve@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.org.theme_header_image = PNG_BYTES
        self.org.theme_header_image_content_type = "image/png"
        self.org.save()
        self.property = Property.objects.create(
            organization=self.org,
            name="Themed",
            boundary=SQUARE,
            is_public=True,
            theme_header_image=PNG_BYTES,
            theme_header_image_content_type="image/png",
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
        self.photo = ActivityPhoto.objects.create(
            activity=self.activity, image=PNG_BYTES, content_type="image/png"
        )
        self.client.force_login(self.user)

    def test_the_theme_image_endpoints_still_serve_the_exact_bytes(self):
        """The byte-serving views are the ones that genuinely read the
        blob. Two of them reach it through a queryset this change touched,
        so they opt back in explicitly rather than relying on a deferred
        attribute load."""
        for url in (
            reverse("org-theme-image"),
            reverse("property-theme-image", args=[self.property.id]),
            reverse("public-organization-theme-image", args=[self.org.id]),
            reverse("public-property-theme-image", args=[self.property.id]),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, PNG_BYTES)
                self.assertEqual(response["Content-Type"], "image/png")

    def test_the_photo_endpoints_still_serve_the_exact_bytes(self):
        response = self.client.get(
            reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PNG_BYTES)

    def test_the_photo_list_still_answers_with_urls(self):
        response = self.client.get(reverse("activity-photos", args=[self.activity.id]))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertIn("url", body[0])
        self.assertEqual(body[0]["content_type"], "image/png")

    def test_has_theme_header_image_is_still_true(self):
        """The boolean the whole deferral depends on — it is derived from
        the content-type column, which is why that one stays loaded."""
        response = self.client.get(f"/api/properties/{self.property.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["properties"]["has_theme_header_image"])

    def test_the_public_property_gate_still_holds(self):
        """`_public_property_or_404` now goes through `Property.objects`
        rather than the bare model class so it can defer. That manager is
        what filters soft-deleted rows, so the gate must be unchanged."""
        self.assertEqual(
            self.client.get(reverse("public-property", args=[self.property.id])).status_code,
            200,
        )

        self.property.deleted_at = timezone.now()
        self.property.save(update_fields=["deleted_at"])
        self.assertEqual(
            self.client.get(reverse("public-property", args=[self.property.id])).status_code,
            404,
            "a soft-deleted property is reachable on the public site again — the "
            "deferral changed which manager the lookup goes through",
        )

        self.property.deleted_at = None
        self.property.is_public = False
        self.property.save(update_fields=["deleted_at", "is_public"])
        self.assertEqual(
            self.client.get(reverse("public-property", args=[self.property.id])).status_code,
            404,
        )


# --- 9. Every image response can be revalidated (D33, 2026-09-14) ---
#
# Nothing this app served carried a cache validator. `image_response`
# returned bytes and a content type and nothing else — no `ETag`, no
# `Last-Modified`, no `Cache-Control` — and `ConditionalGetMiddleware` was
# not installed. Measured in real Chromium before the fix: five views of a
# six-image page were five full downloads and **zero** conditional
# requests. Not "the browser declined to revalidate"; it had nothing to
# revalidate with.
#
# Three wrong fixes are plausible here, and they are caught by disjoint
# tests. Each was built and run against this section.
#
# **Wrong fix A — hash the bytes inside `image_response`.** The obvious
# implementation: no new column, no migration, four lines. It returns a
# correct 304, it cuts network transfer, and **every outcome test below
# passes against it.** What it does not do is the half that matters on a
# 2 MB photo: it still reads the whole blob out of Postgres and hashes it
# on *every* request, including the ones that answer 304 with an empty
# body. Only `test_a_conditional_hit_never_reads_the_blob_column` can tell
# the two apart — nothing about the response can, because the response is
# byte-identical.
#
# **Wrong fix B — compare `If-None-Match` strongly.** `GZipMiddleware`
# (D31, added the previous session) rewrites a strong `ETag` to `W/"..."`
# on any response it actually compresses, so what the app hands out and
# what the client hands back can differ by that prefix. A strong
# comparison therefore never matches on exactly those responses: every
# header is set, the code reads as complete, and it silently returns a
# full body forever. `test_a_weak_validator_still_matches` is the only
# test that goes red.
#
# This was measured on a live server rather than reasoned about, and the
# measurement corrected the guess. The assumption was that JPEG bytes are
# incompressible, so GZipMiddleware would pass them through and the ETag
# would stay strong — making wrong fix B a rare, environment-dependent
# bug. It is not: a real 359,065-byte JPEG compressed by ~2%, which is
# enough for the middleware to keep the compressed response, so the server
# really does hand out `W/"..."` to any client that offers gzip. Wrong fix
# B would therefore re-send **every photo in the app, every time**, while
# passing a test that fetched without `Accept-Encoding`.
#
# **Wrong fix C — reach for the biggest number: `public, max-age=31536000,
# immutable`.** Measured, that really is ~2x better than `no-cache`
# (1 request vs 5, of which 3 were 304s). It is also wrong here, and this
# is D3 resurfacing: Habitat images are **retractable**. A photo can be
# deleted, a property flipped private or soft-deleted, a page
# un-published. A shared-cacheable copy with a long `max-age` is one
# nothing in the app can reach — which was D3's exact finding, that the
# stronger action retracted *less* than the weaker one.
#
# Wrong fix C is worth a note on what a test can and cannot do. The
# server-side gate still runs on every request that arrives, so a
# retraction test passes against C too — the whole problem with C is that
# the request never arrives. That is unobservable from the server, so the
# only thing that can pin it is an assertion about the header itself:
# `test_no_image_path_is_shared_cacheable`. A header assertion usually
# earns its keep by being cheap; this one earns it by being the only
# instrument that can see the defect at all.

import hashlib

from apps.accounts.images import IMAGE_CACHE_CONTROL, image_digest, store_image

# Distinct bytes per fixture so a test that mixes two rows up fails rather
# than passing on a coincidence.
PHOTO_BYTES = b"\x89PNG\r\n\x1a\n" + b"photo-payload" * 8
OTHER_PHOTO_BYTES = b"\x89PNG\r\n\x1a\n" + b"a-different-photo" * 8
BANNER_A = b"\x89PNG\r\n\x1a\n" + b"banner-one" * 8
BANNER_B = b"\x89PNG\r\n\x1a\n" + b"banner-two-is-different" * 8


def _quoted_columns(sql, prefix):
    """Whole quoted column names in `sql` starting with `prefix`.

    Whole names, never a substring test — `"image" in sql` is True when the
    only column present is `image_sha256`, which is the trap D27 and D30
    both hit (in an assertion and in a *filter* respectively, where it is
    much harder to notice). A filter that silently discards the query it
    exists to inspect still leaves something to assert on, which is exactly
    why it hides.
    """
    return {c for c in re.findall(r'"(\w+)"', sql) if c.startswith(prefix)}


class ImageEtagTests(TestCase):
    """Mechanism: what the eight image paths put on the wire."""

    def setUp(self):
        self.org = Organization.objects.create(name="Etag Org")
        self.user = User.objects.create_user(
            email="etag@example.com", password="pw-12345678"
        )
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.org.save(
            update_fields=store_image(
                self.org,
                "theme_header_image",
                "theme_header_image_content_type",
                BANNER_A,
                "image/png",
            )
        )
        self.property = Property.objects.create(
            organization=self.org, name="Themed", boundary=SQUARE, is_public=True
        )
        self.property.save(
            update_fields=store_image(
                self.property,
                "theme_header_image",
                "theme_header_image_content_type",
                BANNER_B,
                "image/png",
            )
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
        self.photo = ActivityPhoto(activity=self.activity)
        store_image(self.photo, "image", "content_type", PHOTO_BYTES, "image/png")
        self.photo.save()

        self.species = Species.objects.create(
            organization=self.org, common_name="Crabgrass"
        )
        self.sighting = Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=self.species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
        )
        self.sighting_photo = SightingPhoto(sighting=self.sighting)
        store_image(
            self.sighting_photo, "image", "content_type", OTHER_PHOTO_BYTES, "image/png"
        )
        self.sighting_photo.save()
        self.client.force_login(self.user)

    def _all_image_urls(self):
        """All eight byte-serving paths D6 enumerated — four authenticated,
        four anonymous. The count is the point: a fix applied to the two
        obvious photo views would leave six paths uncovered."""
        return {
            "org theme": reverse("org-theme-image"),
            "property theme": reverse("property-theme-image", args=[self.property.id]),
            "activity photo": reverse(
                "activity-photo-image", args=[self.activity.id, self.photo.id]
            ),
            "sighting photo": reverse(
                "sighting-photo-image", args=[self.sighting.id, self.sighting_photo.id]
            ),
            "public org theme": reverse(
                "public-organization-theme-image", args=[self.org.id]
            ),
            "public property theme": reverse(
                "public-property-theme-image", args=[self.property.id]
            ),
            "public activity photo": reverse(
                "public-activity-photo-image", args=[self.activity.id, self.photo.id]
            ),
            "public sighting photo": reverse(
                "public-sighting-photo-image",
                args=[self.sighting.id, self.sighting_photo.id],
            ),
        }

    def test_every_image_path_carries_an_etag_and_cache_control(self):
        for label, url in self._all_image_urls().items():
            with self.subTest(path=label):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn(
                    "ETag",
                    response.headers,
                    f"{label} serves no validator, so no request for it can ever "
                    "be conditional",
                )
                self.assertEqual(response.headers["Cache-Control"], IMAGE_CACHE_CONTROL)

    def test_the_etag_is_the_sha256_of_the_exact_bytes_served(self):
        """A content-derived validator, so it cannot go stale. Computed
        here with `hashlib` directly rather than by calling the app's own
        helper, so a change to that helper has to be deliberate."""
        response = self.client.get(
            reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        )

        expected = hashlib.sha256(PHOTO_BYTES).hexdigest()
        self.assertEqual(response.headers["ETag"], f'"{expected}"')
        self.assertEqual(response.content, PHOTO_BYTES)

    def test_two_different_images_get_two_different_etags(self):
        """Guards the degenerate 'fix' of a constant validator, which would
        make every image in the app collide in one cache entry."""
        urls = self._all_image_urls()
        etags = {
            label: self.client.get(url).headers.get("ETag")
            for label, url in urls.items()
        }
        # Four distinct payloads across eight paths: the two photo paths
        # and the two theme paths each appear authenticated and public.
        self.assertEqual(len(set(etags.values())), 4, etags)

    def test_a_matching_validator_gets_a_304_with_no_body(self):
        for label, url in self._all_image_urls().items():
            with self.subTest(path=label):
                etag = self.client.get(url).headers["ETag"]
                response = self.client.get(url, HTTP_IF_NONE_MATCH=etag)

                self.assertEqual(response.status_code, 304)
                self.assertEqual(response.content, b"")
                self.assertEqual(
                    response.headers["ETag"],
                    etag,
                    "a 304 must repeat its validator, or a cache holding the "
                    "original has nothing to refresh its entry with",
                )

    def test_a_stale_validator_gets_the_full_body(self):
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        response = self.client.get(url, HTTP_IF_NONE_MATCH='"not-the-right-digest"')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PHOTO_BYTES)

    def test_a_weak_validator_still_matches(self):
        """The only test that catches wrong fix B.

        `If-None-Match` is specified to use weak comparison, and that is not
        a technicality here: `GZipMiddleware` rewrites a strong `ETag` to
        `W/"..."` on any response it compresses, so this is the literal
        value a real client will send back for such a response.
        """
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        strong = self.client.get(url).headers["ETag"]
        self.assertFalse(strong.startswith("W/"), "fixture assumption")

        response = self.client.get(url, HTTP_IF_NONE_MATCH=f"W/{strong}")

        self.assertEqual(
            response.status_code,
            304,
            "a weak validator did not match its own strong form — every "
            "response GZipMiddleware compresses will re-send in full",
        )

    def test_the_round_trip_works_with_compression_in_the_middle(self):
        """The production shape, end to end: offer gzip, take back whatever
        validator the server actually sent, and send that.

        This is the test closest to what a browser does, and it is here
        because measuring a live server showed the weak form is the *normal*
        case for a photo rather than an exotic one — the JPEG compressed
        just enough for GZipMiddleware to keep the compressed response.
        """
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        first = self.client.get(url, HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(first.status_code, 200)

        echoed = first.headers["ETag"]
        second = self.client.get(
            url, HTTP_ACCEPT_ENCODING="gzip", HTTP_IF_NONE_MATCH=echoed
        )
        self.assertEqual(
            second.status_code,
            304,
            f"a client that echoed back exactly what the server sent ({echoed}) "
            "was sent the whole photo again",
        )

    def test_a_validator_list_and_a_wildcard_both_match(self):
        """Real caches send more than one candidate, and `*` is legal."""
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        etag = self.client.get(url).headers["ETag"]

        listed = self.client.get(
            url, HTTP_IF_NONE_MATCH=f'"something-else", {etag}, W/"another"'
        )
        self.assertEqual(listed.status_code, 304)

        self.assertEqual(self.client.get(url, HTTP_IF_NONE_MATCH="*").status_code, 304)

    def test_a_malformed_validator_is_ignored_rather_than_crashing(self):
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        response = self.client.get(url, HTTP_IF_NONE_MATCH="not a valid etag at all")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PHOTO_BYTES)

    def test_a_conditional_hit_never_reads_the_blob_column(self):
        """The test that catches wrong fix A, and the reason this fix has a
        stored column at all.

        Hashing the body inside `image_response` produces an identical 304
        while still pulling the entire photo out of Postgres to compute the
        hash it then throws away. The response cannot show that; the SQL
        can.
        """
        cases = (
            (
                reverse("activity-photo-image", args=[self.activity.id, self.photo.id]),
                "image",
            ),
            (
                reverse(
                    "sighting-photo-image",
                    args=[self.sighting.id, self.sighting_photo.id],
                ),
                "image",
            ),
            (reverse("org-theme-image"), "theme_header_image"),
            (
                reverse("property-theme-image", args=[self.property.id]),
                "theme_header_image",
            ),
            (
                reverse("public-organization-theme-image", args=[self.org.id]),
                "theme_header_image",
            ),
            (
                reverse("public-property-theme-image", args=[self.property.id]),
                "theme_header_image",
            ),
            (
                reverse(
                    "public-activity-photo-image", args=[self.activity.id, self.photo.id]
                ),
                "image",
            ),
            (
                reverse(
                    "public-sighting-photo-image",
                    args=[self.sighting.id, self.sighting_photo.id],
                ),
                "image",
            ),
        )
        for url, blob_column in cases:
            with self.subTest(url=url):
                etag = self.client.get(url).headers["ETag"]
                with CaptureQueriesContext(connection) as captured:
                    response = self.client.get(url, HTTP_IF_NONE_MATCH=etag)
                self.assertEqual(response.status_code, 304)

                touched = set()
                for query in captured.captured_queries:
                    touched |= _quoted_columns(query["sql"], blob_column)
                self.assertNotIn(
                    blob_column,
                    touched,
                    f"a 304 for {url} still read the blob out of Postgres "
                    f"(columns seen: {sorted(touched)}) — the bytes were loaded "
                    "to answer a request whose whole point is not sending them",
                )

    def test_a_cache_miss_does_read_the_blob(self):
        """The other half of the pair, so the test above can't be satisfied
        by a fix that simply stops serving the image."""
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)

        self.assertEqual(response.content, PHOTO_BYTES)
        touched = set()
        for query in captured.captured_queries:
            touched |= _quoted_columns(query["sql"], "image")
        self.assertIn("image", touched)

    def test_no_image_path_is_shared_cacheable(self):
        """The only instrument that can see wrong fix C.

        The retraction risk is that the request never reaches the server,
        which is by definition unobservable server-side — so the header is
        the only thing left to assert on. `no-cache` means "store it, but
        revalidate before reuse", which keeps the app's own gate
        authoritative on every request.
        """
        for label, url in self._all_image_urls().items():
            with self.subTest(path=label):
                value = self.client.get(url).headers["Cache-Control"]
                self.assertNotIn("max-age", value, label)
                self.assertNotIn("immutable", value, label)
                self.assertNotIn(
                    "public",
                    value,
                    f"{label} may be stored by a shared cache — a retracted "
                    "photo would keep being served from it (D3)",
                )
                self.assertIn("no-cache", value, label)


class ImageDigestIsWrittenWithTheBytesTests(TestCase):
    """Mechanism: a stored digest can never disagree with its own bytes."""

    def setUp(self):
        self.org = Organization.objects.create(name="Digest Org")
        self.user = User.objects.create_user(
            email="digest@example.com", password="pw-12345678"
        )
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org, name="Themed", boundary=SQUARE, is_public=True
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
        self.client.force_login(self.user)

    def test_uploading_a_photo_stores_its_digest(self):
        """Through the real endpoint, not by calling the helper — the
        defect this whole module exists for was a check that was correct in
        isolation and wrong at all four call sites."""
        response = self.client.post(
            reverse("activity-photos", args=[self.activity.id]),
            {"image": SimpleUploadedFile("p.png", PHOTO_BYTES, content_type="image/png")},
        )
        self.assertEqual(response.status_code, 201)

        photo = ActivityPhoto.objects.get(activity=self.activity)
        self.assertEqual(photo.image_sha256, hashlib.sha256(PHOTO_BYTES).hexdigest())

    def test_uploading_a_sighting_photo_stores_its_digest(self):
        species = Species.objects.create(organization=self.org, common_name="Aster")
        sighting = Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
        )
        response = self.client.post(
            reverse("sighting-photos", args=[sighting.id]),
            {"image": SimpleUploadedFile("p.png", PHOTO_BYTES, content_type="image/png")},
        )
        self.assertEqual(response.status_code, 201)

        photo = SightingPhoto.objects.get(sighting=sighting)
        self.assertEqual(photo.image_sha256, hashlib.sha256(PHOTO_BYTES).hexdigest())

    def test_replacing_a_banner_changes_its_validator(self):
        """Theme banners are the reason the validator is content-derived
        rather than `(pk, uploaded_at)`: unlike a photo, a banner is
        replaced **in place**, so a validator tied to the row's identity
        would keep every cache on the old image indefinitely."""
        url = reverse("org-theme-image")
        self.client.post(
            url, {"image": SimpleUploadedFile("a.png", BANNER_A, content_type="image/png")}
        )
        first = self.client.get(url).headers["ETag"]

        self.client.post(
            url, {"image": SimpleUploadedFile("b.png", BANNER_B, content_type="image/png")}
        )
        second = self.client.get(url)

        self.assertNotEqual(first, second.headers["ETag"])
        self.assertEqual(second.content, BANNER_B)
        self.assertEqual(
            self.client.get(url, HTTP_IF_NONE_MATCH=first).status_code,
            200,
            "the old validator still matched after the banner was replaced — "
            "every cache holding it would keep showing the previous image",
        )

    def test_clearing_a_banner_clears_its_digest(self):
        url = reverse("org-theme-image")
        self.client.post(
            url, {"image": SimpleUploadedFile("a.png", BANNER_A, content_type="image/png")}
        )
        self.assertEqual(self.client.delete(url).status_code, 204)

        self.org.refresh_from_db()
        self.assertEqual(self.org.theme_header_image_sha256, "")

    def test_a_row_with_no_digest_serves_a_full_body_without_an_etag(self):
        """The degradation path, pinned so it stays graceful. Nothing
        writes a blank digest today — the migration backfills — but a row
        restored from an older dump would have one, and it must serve
        correctly rather than 500 or hand out an empty validator that
        matches everything."""
        photo = ActivityPhoto.objects.create(
            activity=self.activity, image=PHOTO_BYTES, content_type="image/png"
        )
        self.assertEqual(photo.image_sha256, "")

        url = reverse("activity-photo-image", args=[self.activity.id, photo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PHOTO_BYTES)
        self.assertNotIn("ETag", response.headers)
        self.assertEqual(self.client.get(url, HTTP_IF_NONE_MATCH='""').status_code, 200)

    def test_the_database_backfill_agrees_with_the_python_digest(self):
        """The migration computes the hash in SQL (`encode(sha256(...))`)
        so that a table D32 projects at tens of gigabytes is never pulled
        through a Python loop. That makes it a *second* implementation of
        the same value, and if the two ever disagreed, every backfilled row
        would serve a validator that never matches — a silent, permanent
        half-failure. This is what keeps them honest.
        """
        photo = ActivityPhoto.objects.create(
            activity=self.activity, image=PHOTO_BYTES, content_type="image/png"
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE activities_activityphoto "
                "SET image_sha256 = encode(sha256(image), 'hex') WHERE id = %s",
                [photo.id],
            )
        photo.refresh_from_db()

        self.assertEqual(photo.image_sha256, image_digest(PHOTO_BYTES))
        self.assertEqual(photo.image_sha256, hashlib.sha256(PHOTO_BYTES).hexdigest())


class ImagesAreStillServedCorrectlyTests(TestCase):
    """Outcome: the bytes, types and gates are untouched by all of the
    above. These pass against the pre-fix code too, deliberately — they are
    what stops "delete the endpoint" from being a passing fix, and they
    cover the retraction gates whose correctness is what makes handing out
    a validator safe in the first place."""

    def setUp(self):
        self.org = Organization.objects.create(name="Still Org")
        self.user = User.objects.create_user(
            email="still@example.com", password="pw-12345678"
        )
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org, name="Themed", boundary=SQUARE, is_public=True
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
        self.photo = ActivityPhoto(activity=self.activity)
        store_image(self.photo, "image", "content_type", PHOTO_BYTES, "image/png")
        self.photo.save()
        self.client.force_login(self.user)

    def test_the_bytes_and_type_are_unchanged(self):
        response = self.client.get(
            reverse("activity-photo-image", args=[self.activity.id, self.photo.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PHOTO_BYTES)
        self.assertEqual(response["Content-Type"], "image/png")

    def test_a_preexisting_svg_row_is_still_served_inert(self):
        """D6's guarantee, re-pinned because `image_response` was edited.
        A stored content type still never steers a response header."""
        photo = ActivityPhoto(activity=self.activity)
        photo.image = SVG_BYTES
        photo.content_type = "image/svg+xml"
        photo.image_sha256 = image_digest(SVG_BYTES)
        photo.save()

        response = self.client.get(
            reverse("activity-photo-image", args=[self.activity.id, photo.id])
        )
        self.assertEqual(response["Content-Type"], FALLBACK_CONTENT_TYPE)

    def test_a_retracted_public_photo_is_refused_even_with_a_valid_validator(self):
        """The gate runs on every request including a conditional one, so a
        retraction takes effect immediately rather than after a cache
        expires. (This passes against wrong fix C too — see the section
        note: C's failure is that the request never arrives.)"""
        url = reverse(
            "public-activity-photo-image", args=[self.activity.id, self.photo.id]
        )
        anonymous = Client()
        etag = anonymous.get(url).headers["ETag"]
        self.assertEqual(anonymous.get(url, HTTP_IF_NONE_MATCH=etag).status_code, 304)

        self.property.is_public = False
        self.property.save(update_fields=["is_public"])
        self.assertEqual(anonymous.get(url, HTTP_IF_NONE_MATCH=etag).status_code, 404)

        self.property.is_public = True
        self.property.deleted_at = timezone.now()
        self.property.save(update_fields=["is_public", "deleted_at"])
        self.assertEqual(
            anonymous.get(url, HTTP_IF_NONE_MATCH=etag).status_code,
            404,
            "D3: a soft-deleted property's published photo is served again",
        )

    def test_a_row_deleted_between_the_two_reads_404s_rather_than_500s(self):
        """Serving in two steps (metadata, then bytes only on a miss) opens
        a window the single-query version didn't have. Simulated by having
        the byte fetch raise what a concurrent delete would raise."""
        url = reverse("activity-photo-image", args=[self.activity.id, self.photo.id])

        def vanished(*args, **kwargs):
            raise ActivityPhoto.DoesNotExist

        with mock.patch.object(
            ActivityPhoto.objects, "values_list", side_effect=vanished
        ):
            response = self.client.get(url)

        self.assertEqual(response.status_code, 404)
        # And the endpoint is unharmed once the patch is gone — which is
        # also what proves the patch was really in effect above.
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_a_missing_banner_still_404s(self):
        self.assertEqual(self.client.get(reverse("org-theme-image")).status_code, 404)

    def test_an_anonymous_caller_still_cannot_read_a_private_photo(self):
        self.assertEqual(
            Client()
            .get(reverse("activity-photo-image", args=[self.activity.id, self.photo.id]))
            .status_code,
            403,
        )


# --- 10. Attribution reaches a member, and never the public (D38, 2026-09-16) ---
#
# Habitat has recorded who did what since Phase 1 — eight fields across six
# models, written on every relevant call site — and served exactly one of
# them (`Feedback.submitted_by_email`) to a human. So the app could tell
# you who complained about a button and not who redrew the boundary of a
# restoration site. The sharpest form: `ActivitySerializer.Meta.fields`
# carried `created_at` and `updated_at` and neither `created_by` nor
# `updated_by`. The timestamp travelled and the person didn't.
#
# These tests live here rather than in the four apps whose endpoints they
# cover, because the shared helper they exercise
# (apps/accounts/attribution.py) does — the same reason D14 and D27 are
# here.
#
# **The defect itself is trivially caught** — six tests below simply fail
# with a missing key against the pre-fix code (9 of 126 fail overall; the
# other three are the notification actor and the D27 link-list instance
# noted at the bottom of this comment). That reproduces the defect and says
# nothing about whether the fix is the right one. The interesting question,
# per D22/D27/D28/D33, is what the *attractive wrong fixes* are and which
# test stops each. There are three. They are **not** caught by disjoint
# tests — they are caught by a nested ladder, which is worth stating
# precisely, because what matters is which test is the *only* thing
# standing between each wrong fix and shipping:
#
#     wrong fix      email-search   key-set   base-class   measured
#     1 base ser.    FAIL           FAIL      FAIL         5 of 126 fail
#     2 strip        pass           pass      FAIL         2 of 126 fail
#     3 null flag    pass           FAIL      FAIL         3 of 126 fail
#
# So the base-class test is the only thing that catches fix 2, and the
# key-set test is the only thing that catches fix 3. Delete either and the
# corresponding wrong fix ships silently and green. Fix 2 is the one to
# dwell on: it fails **nothing** that reads a response — every
# authenticated outcome test, both email searches, the key-set test and the
# entire apps.public_site suite pass — because its public response body is
# byte-identical to the real fix's.
#
# Note also what the real fix does *not* touch: `apps/public_site/views.py`
# is unmodified. That is the observable difference between opt-in and
# opt-out, and it is why fix 2 is wrong despite being indistinguishable
# from the outside today.
#
# 1. **Put the fields on the base serializer** (the obvious two-line
#    change). Every authenticated response is then correct — so every
#    outcome test below passes — and `apps/public_site/views.py` starts
#    publishing a member's email on every public activity and sighting,
#    because it renders those same serializers under `AllowAny`. Caught
#    *only* by the public-payload tests. This is D8 re-entered through a
#    different door, and it is invisible in the diff: the change is in
#    apps/activities/, the consequence lands in apps/public_site/.
#
# 2. **Strip the fields in `public_site` instead.** This passes the
#    authenticated tests *and* the public-payload tests — the public
#    response body is byte-identical to the real fix. It is still wrong,
#    because it is an opt-out: the next public endpoint inherits the leak
#    by default. Caught *only* by
#    `test_the_base_serializers_declare_no_attribution`, which asks the
#    class rather than the response — measured at 2 of 126 failing, both
#    subtests of that one test.
#
# 3. **Emit the fields as null publicly** (one serializer, a context flag).
#    No email leaks and the base class check passes. The public payload's
#    key set now advertises that attribution exists and is withheld, and
#    the flag is one forgotten keyword argument away from fix 1. The
#    key-set test is the only one that notices, because no email leaks:
#    `test_the_public_payload_key_set_is_unchanged` pins the exact keys
#    rather than just the absence of an address.
#
# Each was built and run; the measured result is in the task log.
#
# Two further things are pinned here because they are silent if wrong:
#
# **The joins must not re-open D27.** Serving attribution means
# `select_related("created_by")`, and a select_related target is rebuilt
# per row with no dedupe — which is exactly how D27 happened. It is safe
# only because `User` carries no BinaryField, so
# `test_the_user_table_carries_no_blob_column` pins that fact rather than
# leaving a future blob on `User` to be discovered in production. And the
# query count is asserted, because without the joins each row costs its own
# lookup on endpoints D30/D31 measured as this app's volume problem.
#
# **D27's substring trap is live in this section too** — `created_by` is a
# substring of nothing here, but `created_by_id` is a real column beside
# the join, so the column helper matches whole names.


def _selected_columns(sql):
    """Whole quoted column names in a query — see D27's substring trap
    (`"theme_header_image"` matches inside
    `"theme_header_image_content_type"`, so a substring check there can
    never fail)."""
    return set(re.findall(r'"(\w+)"', sql))


class AttributionReachesAMemberTests(TestCase):
    """Outcome: an org member sees who created and last edited a record."""

    def setUp(self):
        self.org = Organization.objects.create(name="Attribution Org")
        self.author = User.objects.create_user(email="author@example.com", password="pw-12345678")
        self.editor = User.objects.create_user(email="editor@example.com", password="pw-12345678")
        for user in (self.author, self.editor):
            Membership.objects.create(
                organization=self.org, user=user, role=Membership.Role.ADMIN
            )
        self.property = Property.objects.create(
            organization=self.org, name="Meadow", boundary=SQUARE, is_public=True
        )
        self.state = WorkflowState.objects.filter(organization=self.org).first()
        self.type = ActivityType.objects.filter(organization=self.org).first()
        self.species = Species.objects.create(organization=self.org, common_name="Bluestem")

    def _activity(self, **kwargs):
        return Activity.objects.create(
            organization=self.org,
            property=self.property,
            activity_type=self.type,
            status=self.state,
            geometry=SQUARE,
            is_public=True,
            **kwargs,
        )

    def _sighting(self, **kwargs):
        return Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=self.species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
            **kwargs,
        )

    def test_an_activity_names_its_creator(self):
        self._activity(created_by=self.author)
        self.client.force_login(self.editor)
        props = self.client.get("/api/activities/").json()["features"][0]["properties"]
        self.assertEqual(props["created_by_email"], "author@example.com")

    def test_an_activity_names_its_last_editor(self):
        """`updated_by` is the only "who last touched this" field in the
        application. It is written on every PATCH and, until D38, had never
        left the database — which is what makes D29 (the form PATCHes every
        field from the snapshot it opened with) silent."""
        activity = self._activity(created_by=self.author)
        self.client.force_login(self.editor)
        self.client.patch(
            f"/api/activities/{activity.id}/",
            data=json.dumps({"properties": {"notes": "fixed a typo"}}),
            content_type="application/json",
        )
        props = self.client.get("/api/activities/").json()["features"][0]["properties"]
        self.assertEqual(props["created_by_email"], "author@example.com")
        self.assertEqual(props["updated_by_email"], "editor@example.com")

    def test_an_unedited_activity_reports_no_editor_rather_than_failing(self):
        """The FKs are SET_NULL and a fresh record has never been edited,
        so null is a real value on a normal path, not an edge case."""
        self._activity(created_by=self.author)
        self.client.force_login(self.author)
        props = self.client.get("/api/activities/").json()["features"][0]["properties"]
        self.assertIsNone(props["updated_by_email"])

    def test_a_sighting_names_its_creator(self):
        self._sighting(created_by=self.author)
        self.client.force_login(self.editor)
        props = self.client.get("/api/sightings/").json()["features"][0]["properties"]
        self.assertEqual(props["created_by_email"], "author@example.com")

    def test_a_link_names_who_made_it(self):
        """The other half of D38's matched pair: `linked_at` was served and
        `linked_by` was not."""
        activity = self._activity(created_by=self.author)
        sighting = self._sighting(created_by=self.author)
        self.client.force_login(self.editor)
        self.client.post(
            f"/api/activities/{activity.id}/links/",
            data=json.dumps({"sighting": sighting.id}),
            content_type="application/json",
        )
        rows = self.client.get(f"/api/activities/{activity.id}/links/").json()
        self.assertEqual(rows[0]["linked_by_email"], "editor@example.com")
        self.assertIn("linked_at", rows[0])

    def test_a_viewer_sees_attribution_too(self):
        """Deliberate, and it discloses nothing new: `MembershipViewSet.list`
        carries no `ensure_role`, so any member can already enumerate every
        member's email via GET /api/org/members/. That was audited as
        intentional and is the premise that makes this safe — this test
        exists so a later "tighten it up" change has to be deliberate."""
        viewer = User.objects.create_user(email="viewer@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=viewer, role=Membership.Role.VIEWER
        )
        self._activity(created_by=self.author)
        self.client.force_login(viewer)
        props = self.client.get("/api/activities/").json()["features"][0]["properties"]
        self.assertEqual(props["created_by_email"], "author@example.com")


class AttributionNeverReachesThePublicTests(TestCase):
    """The trap. Catches wrong fix 1 (fields on the base serializer) and,
    via the key-set test, wrong fix 3 (nulls emitted publicly).

    Every test here passes against the *original* pre-fix code — there was
    no attribution anywhere, so of course none leaked. They exist entirely
    to constrain the fix, which is the D22 shape: a defect and its most
    attractive bad fix need different tests."""

    def setUp(self):
        self.org = Organization.objects.create(name="Public Org")
        self.author = User.objects.create_user(email="author@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.author, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org, name="Preserve", boundary=SQUARE, is_public=True
        )
        state = WorkflowState.objects.filter(organization=self.org).first()
        type_ = ActivityType.objects.filter(organization=self.org).first()
        species = Species.objects.create(organization=self.org, common_name="Bluestem")
        Activity.objects.create(
            organization=self.org,
            property=self.property,
            activity_type=type_,
            status=state,
            geometry=SQUARE,
            is_public=True,
            created_by=self.author,
            updated_by=self.author,
        )
        Sighting.objects.create(
            organization=self.org,
            property=self.property,
            species=species,
            location=Point(0.5, 0.5),
            observed_at=timezone.now(),
            is_public=True,
            created_by=self.author,
        )
        self.anon = Client()

    def _public(self, kind):
        response = self.anon.get(f"/api/public/properties/{self.property.id}/{kind}/")
        self.assertEqual(response.status_code, 200)
        return response.json()["features"][0]["properties"]

    def test_no_email_appears_anywhere_in_the_public_activity_payload(self):
        """Deliberately a search of the whole serialized body rather than a
        key check: a leak could arrive under any field name."""
        body = self.anon.get(
            f"/api/public/properties/{self.property.id}/activities/"
        ).content.decode()
        self.assertNotIn("author@example.com", body)
        # No address at all, not just this one: a leak could arrive under
        # any field name, and nothing in this fixture legitimately
        # contains an "@" (notes are empty).
        self.assertNotIn("@", body)

    def test_no_email_appears_anywhere_in_the_public_sighting_payload(self):
        body = self.anon.get(
            f"/api/public/properties/{self.property.id}/sightings/"
        ).content.decode()
        self.assertNotIn("author@example.com", body)
        self.assertNotIn("@", body)

    def test_the_public_payload_key_set_is_unchanged(self):
        """Catches wrong fix 3 — emitting the fields as null publicly. No
        email leaks there, so every other test in this class passes; only
        an exact key set notices that the public response now advertises
        attribution exists and is being withheld."""
        self.assertEqual(
            self._public("activities").keys() & {"created_by_email", "updated_by_email"}, set()
        )
        self.assertEqual(self._public("sightings").keys() & {"created_by_email"}, set())

    def test_the_base_serializers_declare_no_attribution(self):
        """Catches wrong fix 2 — stripping the fields in `public_site`
        rather than never declaring them.

        This is the only test in the section that can. A strip produces a
        byte-identical public response, so no assertion about the response
        can tell the two apart; the difference is entirely in whether the
        class the next public endpoint reaches for is safe by default.
        Asking the class is the instrument, in D33's sense — the
        consequence of the wrong fix happens in code that doesn't exist
        yet, so the assertion has to move to something observable now."""
        from apps.accounts.attribution import assert_no_attribution
        from apps.activities.serializers import ActivitySerializer
        from apps.sightings.serializers import (
            SightingActivityLinkSerializer,
            SightingSerializer,
        )

        for serializer_class in (
            ActivitySerializer,
            SightingSerializer,
            SightingActivityLinkSerializer,
        ):
            with self.subTest(serializer=serializer_class.__name__):
                self.assertTrue(
                    assert_no_attribution(serializer_class),
                    f"{serializer_class.__name__} is served to AllowAny callers (or is one "
                    "import away from being); attribution belongs on its WithAttribution "
                    "subclass, not on the base — see apps/accounts/attribution.py",
                )

    def test_the_public_site_still_serves_its_records(self):
        """Guards against the degenerate "fix" of removing the public
        endpoints, which would satisfy every other test in this class."""
        activities = self.anon.get(
            f"/api/public/properties/{self.property.id}/activities/"
        ).json()["features"]
        sightings = self.anon.get(
            f"/api/public/properties/{self.property.id}/sightings/"
        ).json()["features"]
        self.assertEqual(len(activities), 1)
        self.assertEqual(len(sightings), 1)
        self.assertIn("notes", activities[0]["properties"])
        self.assertIn("observed_at", sightings[0]["properties"])


class AttributionCostsNoExtraQueriesTests(TestCase):
    """Mechanism: the joins are real, and they don't re-open D27."""

    def setUp(self):
        self.org = Organization.objects.create(name="Query Org")
        self.user = User.objects.create_user(email="q@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=self.user, role=Membership.Role.ADMIN
        )
        self.property = Property.objects.create(
            organization=self.org,
            name="Themed",
            boundary=SQUARE,
            is_public=True,
            theme_header_image=BANNER_BYTES,
            theme_header_image_content_type="image/png",
        )
        state = WorkflowState.objects.filter(organization=self.org).first()
        type_ = ActivityType.objects.filter(organization=self.org).first()
        for _ in range(12):
            Activity.objects.create(
                organization=self.org,
                property=self.property,
                activity_type=type_,
                status=state,
                geometry=SQUARE,
                is_public=True,
                created_by=self.user,
                updated_by=self.user,
            )
        self.client.force_login(self.user)

    def test_listing_activities_costs_a_constant_number_of_queries(self):
        """Without `select_related`, each row's `created_by.email` is its
        own query — 12 rows, 24 extra lookups — on an endpoint that is
        org-wide and unpaginated (D30/D31)."""
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/activities/")
        self.assertEqual(len(response.json()["features"]), 12)
        # Measured: 8 queries with the joins, 32 without (12 rows x 2
        # attribution fields = 24 extra lookups). The bound is loose
        # enough to survive an unrelated query being added and tight
        # enough that per-row fetching cannot fit under it.
        self.assertLess(
            len(ctx.captured_queries),
            12,
            "attribution is being fetched per row — the select_related is missing",
        )

    def test_the_attribution_join_does_not_load_image_bytes(self):
        """D28's lesson: D27's invariant is a property of each query, so
        every new join to a blob-bearing table re-opens it. This one joins
        `User`, which has no blob — but the assertion is on the SQL, not on
        that reasoning, so it stays true if someone adds one."""
        with CaptureQueriesContext(connection) as ctx:
            self.client.get("/api/activities/")
        row_queries = [q["sql"] for q in ctx.captured_queries if "accounts_user" in q["sql"]]
        self.assertTrue(row_queries, "expected the activity list to join accounts_user")
        for sql in row_queries:
            self.assertNotIn(
                "theme_header_image",
                _selected_columns(sql),
                "the blob column is back in a list query — see apps/accounts/blobs.py",
            )

    def test_the_user_table_carries_no_blob_column(self):
        """The load-bearing fact behind every `select_related` this change
        adds. A select_related target is rebuilt per row and Django does
        not dedupe it, so a BinaryField on `User` would make each
        attribution join cost that blob once per row — D27 exactly. If this
        ever goes red, apps/accounts/blobs.py needs a fourth column and
        every query in apps/accounts/attribution.py's lists needs a defer."""
        from django.db import models as django_models

        blobs = [
            f.name for f in User._meta.get_fields() if isinstance(f, django_models.BinaryField)
        ]
        self.assertEqual(blobs, [])

    def test_the_link_list_does_not_load_the_property_banner(self):
        """A D27 instance the 2026-09-13 sweep missed, found while adding
        the `linked_by` join beside it: both link list queries
        `select_related("activity__property")` to serve
        `activity_property_name`, and Property carries the banner blob."""
        state = WorkflowState.objects.filter(organization=self.org).first()
        activity = Activity.objects.filter(organization=self.org).first()
        species = Species.objects.create(organization=self.org, common_name="Bluestem")
        for _ in range(3):
            sighting = Sighting.objects.create(
                organization=self.org,
                property=self.property,
                species=species,
                location=Point(0.5, 0.5),
                observed_at=timezone.now(),
                created_by=self.user,
            )
            self.client.post(
                f"/api/activities/{activity.id}/links/",
                data=json.dumps({"sighting": sighting.id}),
                content_type="application/json",
            )
        self.assertIsNotNone(state)
        with CaptureQueriesContext(connection) as ctx:
            rows = self.client.get(f"/api/activities/{activity.id}/links/").json()
        self.assertEqual(len(rows), 3)
        joined = [q["sql"] for q in ctx.captured_queries if "accounts_property" in q["sql"]]
        self.assertTrue(joined, "expected the link list to join accounts_property")
        for sql in joined:
            self.assertNotIn("theme_header_image", _selected_columns(sql))


class AssignmentNotificationNamesTheActorTests(TestCase):
    """The cheapest improvement in the D38 cluster: `Notification` has no
    actor column, and the message was passive — built at a call site
    holding `request.user`."""

    def setUp(self):
        self.org = Organization.objects.create(name="Task Org")
        self.assigner = User.objects.create_user(
            email="assigner@example.com", password="pw-12345678"
        )
        self.assignee = User.objects.create_user(
            email="assignee@example.com", password="pw-12345678"
        )
        for user in (self.assigner, self.assignee):
            Membership.objects.create(
                organization=self.org, user=user, role=Membership.Role.ADMIN
            )
        self.client.force_login(self.assigner)

    def _create_task(self, **body):
        return self.client.post(
            "/api/tasks/",
            data=json.dumps({"title": "Pull garlic mustard", **body}),
            content_type="application/json",
        )

    def _messages(self):
        from apps.notifications.models import Notification

        return list(Notification.objects.values_list("message", flat=True))

    def test_assigning_a_task_names_who_assigned_it(self):
        self.assertEqual(self._create_task(assigned_to=self.assignee.id).status_code, 201)
        self.assertEqual(
            self._messages(),
            ['assigner@example.com assigned you the task "Pull garlic mustard".'],
        )

    def test_reassigning_names_the_reassigner_not_the_original_assigner(self):
        """The actor is whoever made *this* change, which is the whole
        point — `perform_update`'s notify must not quietly reuse
        `task.created_by`."""
        third = User.objects.create_user(email="third@example.com", password="pw-12345678")
        Membership.objects.create(
            organization=self.org, user=third, role=Membership.Role.ADMIN
        )
        task_id = self._create_task().json()["id"]
        self.client.force_login(third)
        self.client.patch(
            f"/api/tasks/{task_id}/",
            data=json.dumps({"assigned_to": self.assignee.id}),
            content_type="application/json",
        )
        self.assertEqual(
            self._messages(),
            ['third@example.com assigned you the task "Pull garlic mustard".'],
        )

    def test_assigning_a_task_to_yourself_still_notifies_nobody(self):
        """Pre-existing behaviour, pinned so the message change can't have
        quietly removed the self-assignment guard and started telling
        people what they just did."""
        self.assertEqual(self._create_task(assigned_to=self.assigner.id).status_code, 201)
        self.assertEqual(self._messages(), [])

    def test_the_task_list_still_names_the_creator(self):
        """`Task.created_by_email` was already in the serializer and
        rendered in zero components — delivered, never displayed (D28's
        distinction). Pinned so the field a frontend now reads can't be
        dropped as unused."""
        self._create_task()
        rows = self.client.get("/api/tasks/").json()
        self.assertEqual(rows[0]["created_by_email"], "assigner@example.com")


# --- 11. The two hashing endpoints are rate-limited (D40, 2026-09-17) ---
#
# Until this section existed, the string "throttle" appeared nowhere in the
# backend. Habitat's six other limits are all per-request *size* caps —
# MAX_PHOTO_BYTES, MAX_LOGO_PIXELS, CUSTOM_PAGE_HTML_MAX_BYTES and so on —
# so the app could say "this one request is too big" and could never say
# "you have asked too many times".
#
# That was survivable everywhere except `login_view` and `signup`, the only
# unauthenticated endpoints that run a deliberately-slow KDF. Measured on
# this repo's pinned Django 5.2.17 (median of 8): ~582 ms to check a
# password, ~584 ms to make one — under two attempts per second per core.
# And `ModelBackend.authenticate` hashes against a throwaway user when the
# email does not exist, deliberately (Django #20760), so the cost is paid
# for *any* address: ~400 request bytes buy ~600 ms of server CPU, with no
# account, no valid email and no knowledge of the instance. Confirmed on
# the live host at 1.09 s against a 0.34–0.52 s control.
#
# **What makes this section's shape unusual is the inversion.** D17 was
# fixed by bounding the resource — cap the pixels, decode less. Here the
# expense *is* the security control, so there is no cheaper-hash fix and
# the only remedy is bounding the rate. That means most of what could go
# wrong is not "the limit is absent" but "the limit is present and does
# nothing", and every one of those failures returns a perfectly ordinary
# 429 on the happy path of a test. So the tests below are split:
#
#   - three *outcome* tests (a burst is refused, an under-limit burst is
#     not, a refused signup writes nothing), which any plausible fix
#     passes; and
#   - five *mechanism* tests, each of which is the only thing standing
#     between the real fix and one specific attractive wrong one.
#
# Five plausible wrong fixes were built and run against this section, per
# the D17/D18/D27/D38 discipline. D38's correction applies in advance:
# "caught by disjoint tests" is a claim to measure, not to assert. The
# first draft of this comment predicted a tidy one-test-each table and
# **measurement contradicted it twice**, so what follows is what actually
# went red (out of 16):
#
#   | wrong fix                                  | red | the load-bearing test |
#   |--------------------------------------------|-----|-----------------------|
#   | check the limit in the view, after auth    |  1  | never_reaches_the_hash|
#   | leave NUM_PROXIES at DRF's default (None)  |  1  | forwarded_for_not_... |
#   | one global bucket, no key at all           |  2  | different_address_... |
#   | DRF's AnonRateThrottle                     |  5  | session_does_not_bypass|
#   | key the bucket on the submitted email      |  7  | per_address_not_per_email|
#
# **The two rows worth staring at are the ones with a 1.** Delete that
# single test and the wrong fix ships green: a limit checked after
# `authenticate` returns a byte-identical 429 while spending the identical
# ~600 ms, and DRF's default NUM_PROXIES leaves a throttle that is present,
# visible in the diff, and does nothing at all against anyone who sets one
# header. Neither is visible in any response.
#
# **Both predictions that were wrong were wrong in the same direction** —
# they assumed a wrong fix fails only where you aimed at it, and both
# surprises came from signup:
#
#   - The email-keyed fix was predicted to pass every signup test and
#     `a_different_address_has_its_own_budget`. It fails all of them. The
#     signup tests name a *new* address each time (as a real attacker
#     would), so an email-keyed bucket never fills; and that address test
#     reuses one email from two addresses, so the second address arrives
#     already spent.
#   - AnonRateThrottle was predicted to fail only the authenticated-session
#     test. It also takes out every signup test — because `signup` calls
#     `login()`, so from the second request onward the caller *is*
#     authenticated and AnonRateThrottle exempts them. The endpoint whose
#     abuse creates permanent, unremovable tenants is precisely the one
#     that class would leave unlimited.
#
# The email-keyed fix still deserves its reputation as the attractive one:
# it reads as "limit attempts on this account", which sounds stricter. It
# is backwards — the email is a free-text field of the very request being
# limited, so an attacker varies it and is never throttled, while the real
# user, who types the same address every time, is the only person refused.
#
# Two mechanical notes that cost real time to find:
#
# **Throttle state is process-global.** There is no CACHES setting, so it
# lives in one LocMemCache dict for the whole test run. Adding the signup
# throttle failed two unrelated D8 tests immediately (`429 != 201`) because
# between them they sign up more times than the hourly limit allows. That
# is fixed centrally rather than here — config/test_runner.py clears the
# cache before every test — and config/tests.py pins that the runner is
# still configured, because without it the symptom is order-dependent
# failures in whichever module happens to run next.
#
# **The fast hasher below is for speed, not realism.** These tests care
# about whether the hash is reached, not how long it takes, and at the real
# 1,000,000 iterations this section alone would add roughly half a minute
# to the suite. `test_a_refused_login_never_reaches_the_password_hash`
# counts calls, so it is unaffected by which hasher those calls would use.

LOGIN_LIMIT = 10  # requests per minute, per address
SIGNUP_LIMIT = 5  # requests per hour, per address


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class LoginIsRateLimitedTests(TestCase):
    URL = "/api/auth/login/"

    def setUp(self):
        self.user = User.objects.create_user(
            email="member@example.com", password="correct-horse-battery"
        )

    def _attempt(self, email="member@example.com", password="wrong", **extra):
        return self.client.post(
            self.URL, {"email": email, "password": password},
            content_type="application/json", **extra,
        )

    def test_a_burst_of_failed_logins_is_eventually_refused(self):
        """Outcome. The limit is hardcoded here rather than derived from
        LOGIN_RATE on purpose: reading the number out of the code under
        test would let someone raise it to 1000/min and still see green."""
        for i in range(LOGIN_LIMIT):
            self.assertEqual(self._attempt().status_code, 401, f"attempt {i + 1}")
        self.assertEqual(self._attempt().status_code, 429)

    def test_a_correct_password_under_the_limit_still_signs_you_in(self):
        """The direction that breaks people rather than protecting them.
        A limit that refuses a legitimate sign-in is a worse bug than the
        one being fixed, and it would look identical to a broken login."""
        for _ in range(LOGIN_LIMIT - 1):
            self._attempt()
        ok = self._attempt(password="correct-horse-battery")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["user"]["email"], "member@example.com")

    def test_the_refusal_says_when_to_come_back(self):
        """D13/D21's class: a control that refuses must not read as a
        control that is broken. Asserts the shape of the advice, not the
        sentence — the copy can be reworded freely, but it has to keep
        naming a time and keep pointing at the way out that does not
        involve waiting.

        `Retry-After` is checked too because it is the machine-readable
        half of the same promise, and DRF only sets it when `wait` is not
        None — which a throttle subclass can accidentally lose."""
        for _ in range(LOGIN_LIMIT):
            self._attempt()
        refused = self._attempt()

        self.assertEqual(refused.status_code, 429)
        detail = refused.json()["detail"].lower()
        self.assertIn("try again", detail)
        self.assertRegex(detail, r"\d+ (second|minute)")
        self.assertNotRegex(detail, r"\b0 second")
        # Names the control by the label actually on the screen, rather
        # than describing it: the refusal renders directly above that link
        # on the sign-in page (checked in a browser, 390px), so a reader
        # can act on it without interpreting anything. `password_reset_request`
        # runs no hash and is deliberately unthrottled, which is what makes
        # "still works" true rather than optimistic.
        self.assertIn("forgot your password?", detail)
        self.assertIn("Retry-After", refused.headers)

        # The one an earlier version of this section missed, and it took a
        # live server to find: DRF's `Throttled.__init__` appends its own
        # "Expected available in N seconds." to any detail it is given
        # whenever `wait` is set, so the first working version of this
        # refusal stated the wait twice, in two registers —
        #
        #   "...Try again in about 58 seconds. ... Expected available in
        #    58 seconds."
        #
        # — and every assertion above passed against it, because each one
        # checks that some advice is *present*. Nothing that reads a
        # response for a missing thing can see a duplicated thing.
        self.assertNotIn("expected available", detail)
        self.assertEqual(
            len(re.findall(r"\d+ (?:second|minute)", detail)),
            1,
            f"the refusal names the wait more than once: {detail!r}",
        )

    def test_a_refused_login_never_reaches_the_password_hash(self):
        """MECHANISM — and the whole point of the feature.

        Catches: a limit checked inside the view, after `authenticate`.
        That returns the same 429 with the same body while spending the
        same ~600 ms per request, so every outcome test above passes
        against it and nothing else in this suite can tell the difference.
        D17's ordering lesson, in the one place where ordering *is* the
        fix rather than an optimisation of it.

        DRF runs throttles in `APIView.initial()`, before the handler, so
        the refused request must not call `authenticate` at all.
        """
        with mock.patch(
            "apps.accounts.views.authenticate", wraps=views.authenticate
        ) as auth:
            for _ in range(LOGIN_LIMIT):
                self._attempt()
            self.assertEqual(auth.call_count, LOGIN_LIMIT)

            self.assertEqual(self._attempt().status_code, 429)
            self.assertEqual(
                auth.call_count,
                LOGIN_LIMIT,
                "the refused request paid for a password hash it should never have reached",
            )

    def test_the_limit_is_per_address_not_per_email(self):
        """MECHANISM. Catches: keying the bucket on the submitted email.

        Every request here comes from one address and names a different
        account, which is exactly what credential-stuffing looks like and
        exactly what an email-keyed limit lets through unbounded."""
        for i in range(LOGIN_LIMIT):
            self.assertEqual(self._attempt(email=f"stuffed{i}@example.com").status_code, 401)
        self.assertEqual(self._attempt(email="stuffed-final@example.com").status_code, 429)

    def test_a_different_address_has_its_own_budget(self):
        """MECHANISM. Catches: one global bucket, keyed on nothing.

        That fix looks right from the outside — a burst is refused, the
        message is fine — and it would let a single attacker lock every
        user in the world out of signing in. Measured: it is the only
        login test that catches it.

        (The first draft of this docstring claimed an email-keyed fix
        passes here. It does not: this test reuses one email across two
        addresses, so the second address arrives with the bucket already
        spent. Kept as written — the correction is in the section comment.)
        """
        for _ in range(LOGIN_LIMIT + 1):
            self._attempt(REMOTE_ADDR="10.0.0.1")
        self.assertEqual(self._attempt(REMOTE_ADDR="10.0.0.1").status_code, 429)
        self.assertEqual(self._attempt(REMOTE_ADDR="10.0.0.2").status_code, 401)

    def test_x_forwarded_for_is_not_trusted_by_default(self):
        """MECHANISM. Catches: leaving NUM_PROXIES at DRF's own default.

        DRF's default is None, which means "if X-Forwarded-For is present,
        key on the whole chain". That header is set by the client, so an
        attacker varies it per request and is never throttled — the
        throttle is installed, visible in the code, and does nothing.
        NUM_PROXIES=0 pins the key to REMOTE_ADDR.

        The second half asserts the setting is honoured rather than
        ignored: a deployment that declares one proxy must get the address
        that proxy saw, or a real deployment's limit becomes global.
        """
        for i in range(LOGIN_LIMIT):
            self._attempt(HTTP_X_FORWARDED_FOR=f"203.0.113.{i}")
        self.assertEqual(
            self._attempt(HTTP_X_FORWARDED_FOR="203.0.113.99").status_code,
            429,
            "a client-supplied header bought itself a fresh budget",
        )

        with override_settings(REST_FRAMEWORK={**settings.REST_FRAMEWORK, "NUM_PROXIES": 1}):
            self.assertEqual(
                self._attempt(HTTP_X_FORWARDED_FOR="198.51.100.7").status_code,
                401,
                "with a proxy declared, the client address is the one the proxy reported",
            )

    def test_an_authenticated_session_does_not_bypass_the_limit(self):
        """MECHANISM. Catches: using DRF's AnonRateThrottle.

        That class returns None — no throttling whatsoever — the moment
        `request.user` is authenticated, and `login_view` is AllowAny, so a
        request carrying any valid session cookie reaches the same hash.
        One free signup would buy unlimited attempts."""
        self.client.force_login(self.user)
        for _ in range(LOGIN_LIMIT):
            self._attempt(email="someone-else@example.com")
        self.assertEqual(self._attempt(email="someone-else@example.com").status_code, 429)

    def test_endpoints_that_were_not_measured_are_not_throttled(self):
        """There is deliberately no DEFAULT_THROTTLE_CLASSES. This bounds
        the two endpoints that were measured — a global default would
        quietly cap ordinary use of the app, which nobody asked for and
        which nothing here measured the cost of."""
        for _ in range(LOGIN_LIMIT * 3):
            self.assertEqual(self.client.get("/api/auth/csrf/").status_code, 200)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class SignupIsRateLimitedTests(TestCase):
    URL = "/api/auth/signup/"

    def _signup(self, n, **extra):
        return self.client.post(
            self.URL,
            {"email": f"new{n}@example.com", "password": "correct-horse-battery-staple"},
            content_type="application/json",
            **extra,
        )

    def test_signup_is_refused_past_the_hourly_limit(self):
        for i in range(SIGNUP_LIMIT):
            self.assertEqual(self._signup(i).status_code, 201, f"signup {i + 1}")
        self.assertEqual(self._signup(99).status_code, 429)

    def test_a_refused_signup_writes_nothing(self):
        """Signup is the write amplifier, not just a hash: each one creates
        14 rows (User, Organization, Membership, 3 WorkflowStates, 8
        ActivityTypes from the seeding receivers) and **nothing in the app
        can ever remove them** — there is no OrganizationViewSet, no
        account closure and no user deletion outside Django admin. So the
        thing worth pinning is not the status code but that a refusal
        leaves no tenant behind."""
        for i in range(SIGNUP_LIMIT):
            self._signup(i)
        before = (User.objects.count(), Organization.objects.count())

        self.assertEqual(self._signup(99).status_code, 429)
        self.assertEqual((User.objects.count(), Organization.objects.count()), before)
        self.assertFalse(User.objects.filter(email="new99@example.com").exists())

    def test_the_refusal_points_an_existing_user_at_signing_in(self):
        for i in range(SIGNUP_LIMIT):
            self._signup(i)
        detail = self._signup(99).json()["detail"].lower()
        self.assertIn("try again", detail)
        self.assertRegex(detail, r"\d+ (second|minute)")
        self.assertIn("sign in", detail)

    def test_signing_up_does_not_spend_the_login_budget(self):
        """Separate scopes, separate buckets. Sharing one would mean a
        household creating two accounts could not then sign in to either,
        which is a support ticket rather than a security property."""
        for i in range(SIGNUP_LIMIT):
            self._signup(i)
        self.assertEqual(self._signup(99).status_code, 429)

        refused_login = self.client.post(
            "/api/auth/login/",
            {"email": "new0@example.com", "password": "nope"},
            content_type="application/json",
        )
        self.assertEqual(refused_login.status_code, 401)


class RateConstantsTests(SimpleTestCase):
    """Pins the two numbers themselves.

    Not redundant with the burst tests above, and the distinction is the
    reason this class exists: those count to a hardcoded 10 and 5, so
    *tightening* a rate makes them fail loudly. Loosening one to 1000/min
    would leave every one of them green, because they only ever send
    eleven requests. Only an assertion on the constant catches that — the
    D33 case where the observable has to move to the thing you can see.
    """

    def test_the_rates_are_the_ones_that_were_reasoned_about(self):
        self.assertEqual(throttling.LOGIN_RATE, f"{LOGIN_LIMIT}/min")
        self.assertEqual(throttling.SIGNUP_RATE, f"{SIGNUP_LIMIT}/hour")

    def test_the_retry_phrase_never_tells_someone_to_wait_zero_seconds(self):
        """`wait` is a float and is a fraction of a second at the boundary,
        which truncates to "in about 0 seconds" — advice that reads as a
        malfunction. Also checks the minutes branch, because "in about 300
        seconds" is technically true and useless."""
        self.assertEqual(throttling._retry_phrase(0.0), "in about 1 second")
        self.assertEqual(throttling._retry_phrase(0.4), "in about 1 second")
        self.assertEqual(throttling._retry_phrase(29.2), "in about 30 seconds")
        self.assertEqual(throttling._retry_phrase(300.0), "in about 6 minutes")
        self.assertEqual(throttling._retry_phrase(None), "in about 1 second")

    def test_the_other_hashing_paths_are_deliberately_not_throttled(self):
        """`password_reset_confirm` and `invitation_accept` also hash a
        password, and both are protected by entropy rather than by rate: a
        `secrets.token_urlsafe(32)` is 256 bits, so guessing is infeasible
        whatever the rate. Throttling them would lock a legitimate invitee
        out of a link they are holding, for no security gain. Pinned so
        "be consistent" doesn't quietly become the wrong fix."""
        for view in (views.password_reset_confirm, views.invitation_accept):
            self.assertEqual(
                getattr(view.cls, "throttle_classes", []),
                [],
                f"{view.__name__} gained a throttle it does not need",
            )
