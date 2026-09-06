"""Which image types Habitat accepts on upload, and how it serves them back.

This module exists because the same one-line check was copy-pasted into all
four upload endpoints (activity photos, sighting photos, and the org and
property theme banners) and the value it tested was the wrong one:

    if not (image.content_type or "").startswith("image/"):

`UploadedFile.content_type` is the `Content-Type` header of the multipart
part the *client* sent — not anything the server derives from the bytes. So
the client chose the string, `image/svg+xml` passed, and every serving path
then handed that same client-chosen string straight back as the response
`Content-Type`. SVG is not an inert raster format: it can carry `<script>`,
and a browser *navigating* to such a URL (as opposed to loading it in an
`<img>`, which never executes script) runs that script on whatever origin
served it. Habitat serves its app, API and public site from one origin by
default, so that is the app's own origin — and the public photo endpoints
are `AllowAny`, giving such a file a stable, shareable, unauthenticated URL.

Two halves, both needed, and the second is not redundant:

* `validate_image_upload` allowlists the raster types the product actually
  wants, so nothing new is stored with a dangerous type.
* `image_response` serves the *allowlisted* value rather than echoing the
  stored string, so a row written before this module existed cannot still
  steer a response header.

**Why an allowlist on the declared type is sufficient, rather than sniffing
the bytes:** Django sets `X-Content-Type-Options: nosniff` by default
(`SECURE_CONTENT_TYPE_NOSNIFF` is unset in settings.py and defaults to
True). Uploading SVG *bytes* under a declared `image/png` therefore gets
served as `image/png` and the browser will not sniff its way back to SVG —
it renders nothing and executes nothing. The allowlist and `nosniff` are
load-bearing together; if a future change ever turns `nosniff` off, this
module's guarantee weakens and content sniffing becomes the hole again.
"""

# The raster types a phone camera and an ordinary screenshot actually
# produce. Deliberately no `image/svg+xml` (scriptable — the whole reason
# this module exists) and no `image/*` wildcard, so adding a format is a
# considered edit here rather than something a client can assert.
ALLOWED_IMAGE_TYPES = ("image/png", "image/jpeg", "image/webp", "image/gif")

# Non-standard spellings seen from real clients, mapped to the canonical
# type they mean. An alias only ever resolves to a member of the allowlist
# above — it never widens what is accepted.
_ALIASES = {"image/jpg": "image/jpeg", "image/pjpeg": "image/jpeg"}

# What a stored value that isn't on the allowlist is served as instead of
# being echoed back. `application/octet-stream` renders as nothing in an
# `<img>` and downloads rather than executes on navigation, so a row that
# predates the allowlist is inert without having to be deleted or migrated.
FALLBACK_CONTENT_TYPE = "application/octet-stream"

UNSUPPORTED_TYPE_MESSAGE = (
    "Only PNG, JPEG, WebP and GIF images are supported."
)


def normalize_image_type(raw):
    """Canonical form of a `Content-Type` value, or "" if it isn't one we
    accept.

    Strips any parameters (`image/jpeg; charset=binary`), lowercases, and
    resolves the aliases above. Returns "" — never the input — for anything
    not on the allowlist, so a caller can't accidentally pass an unknown
    value through by treating a falsy result as "use what they gave me".
    """
    value = (raw or "").split(";")[0].strip().lower()
    value = _ALIASES.get(value, value)
    return value if value in ALLOWED_IMAGE_TYPES else ""


def validate_image_upload(uploaded_file):
    """The content type to store for `uploaded_file`, or "" to reject it.

    Callers pair this with their own size limit, which differs per endpoint
    (8MB for photos, 5MB for theme banners) and so stays at the call site.
    """
    return normalize_image_type(getattr(uploaded_file, "content_type", ""))


def image_content_type(stored):
    """The `Content-Type` to serve a stored image under.

    Never returns the stored string itself: either an allowlisted value or
    the inert fallback.
    """
    return normalize_image_type(stored) or FALLBACK_CONTENT_TYPE


def image_response(data, stored_content_type):
    """An `HttpResponse` of raw image bytes, served under a type this module
    vouches for rather than one a client chose."""
    # Imported here rather than at module scope purely to keep this module
    # importable by code that isn't serving HTTP (the tests exercise the
    # normalizer directly).
    from django.http import HttpResponse

    return HttpResponse(bytes(data), content_type=image_content_type(stored_content_type))
