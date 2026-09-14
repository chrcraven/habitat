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
    vouches for rather than one a client chose.

    Prefer `serve_image` — this is the unconditional half, and a caller
    using it directly sends a full body to a client that may already hold
    the identical bytes.
    """
    # Imported here rather than at module scope purely to keep this module
    # importable by code that isn't serving HTTP (the tests exercise the
    # normalizer directly).
    from django.http import HttpResponse

    response = HttpResponse(
        bytes(data), content_type=image_content_type(stored_content_type)
    )
    response.headers["Cache-Control"] = IMAGE_CACHE_CONTROL
    return response


# ---------------------------------------------------------------------------
# Cache validators (D33)
# ---------------------------------------------------------------------------
#
# Nothing this app served used to carry one. No `ETag`, no `Last-Modified`,
# no `Cache-Control` — so a browser had nothing to revalidate *with*, and
# every view of a page re-downloaded every photo on it in full, which on the
# server side is a full blob read back out of Postgres. Measured in real
# Chromium: five views of a six-image page were five full downloads and zero
# conditional requests. Not "the browser chose not to revalidate" — it could
# not.
#
# Two decisions here are load-bearing and easy to undo by accident.
#
# **1. `private, no-cache` everywhere, deliberately — not `max-age`, not
# `immutable`, and not a per-route policy.** `no-cache` does not mean "don't
# store"; it means "store it, but revalidate before reuse", which is what
# turns a full body into a 304 while keeping the app's own answer
# authoritative on every single request. The stronger caching directives buy
# roughly 2x more (measured: 1 request vs. 5, against 3 of 5 returning 304)
# and they are wrong here, because Habitat images are **retractable**: a
# photo can be deleted, a property can be flipped private or soft-deleted,
# and a public page can be un-published. A `public, max-age=<large>` on a
# publicly retractable photo would leave a copy in a shared cache that
# nothing in the app can reach — which is D3 exactly, whose whole finding
# was that the stronger action (deleting a property) retracted *less* than
# the weaker one (marking it private).
#
# It is uniform across all eight paths on purpose. Retractability is a
# property of the *record*, not of the route, so a per-route policy table is
# a thing to get wrong rather than a saving; `immutable` on the four
# authenticated photo routes would still be wrong the moment an admin
# deletes a photo.
#
# **2. The ETag is a stored column, not a hash of the bytes.** Hashing the
# body inside this function is the obvious implementation and it is a fix
# that half-works: it returns a correct 304 and it does cut transfer, but it
# still reads the entire blob out of Postgres and hashes it on every
# request, which is the cost that actually matters for a 2 MB photo. Every
# assertion about status codes and response bodies passes against it. So the
# digest is computed once, at upload, and stored beside the content type —
# and the byte-serving views load metadata only, answer a hit without ever
# touching the blob column, and pass a callable that fetches the bytes just
# on a miss. `test_a_conditional_hit_never_reads_the_blob_column` is what
# separates the two; nothing about the response can.
IMAGE_CACHE_CONTROL = "private, no-cache"

# Suffix convention: the digest column for a blob column `x` is always
# `x_sha256`, which is what lets `store_image` below derive it rather than
# taking a fourth field name.
DIGEST_FIELD_SUFFIX = "_sha256"


def image_digest(data):
    """Hex SHA-256 of stored image bytes, or "" for absent bytes.

    Content-derived rather than metadata-derived on purpose. `(pk,
    uploaded_at)` would be a valid validator for photos *today*, because
    photos happen to be immutable — there is no PATCH on one anywhere — but
    that is an invariant held by the absence of a route rather than by
    anything enforcing it, and the failure mode if someone adds one is a
    cache serving the wrong image indefinitely. A content hash cannot go
    stale: if the bytes change, `store_image` recomputes it, and the theme
    banners *are* replaced in place.
    """
    import hashlib

    if data is None:
        return ""
    return hashlib.sha256(bytes(data)).hexdigest()


def store_image(instance, blob_field, content_type_field, data, content_type):
    """Write an image's bytes, type and digest together; return the field
    names to pass as `update_fields`.

    The three values are one fact, and this function exists so they cannot
    drift apart — which is the same reason the rest of this module exists.
    The original defect here was one content-type check copy-pasted into
    four upload endpoints, testing the wrong value in all four; a digest
    assigned at four call sites would be the identical shape of mistake,
    and a row whose digest disagreed with its bytes would serve a stale
    image from cache with nothing on screen to explain it.

    Pass `data=None` to clear (the DELETE paths) — the digest clears with
    it, so an emptied banner cannot keep answering with its old validator.
    """
    digest_field = f"{blob_field}{DIGEST_FIELD_SUFFIX}"
    setattr(instance, blob_field, data)
    setattr(instance, content_type_field, content_type)
    setattr(instance, digest_field, image_digest(data))
    return [blob_field, content_type_field, digest_field]


def _without_weak_prefix(etag):
    return etag[2:] if etag.startswith("W/") else etag


def etag_matches(if_none_match_header, etag):
    """Whether an `If-None-Match` header satisfies `etag`.

    Uses RFC 9110's **weak** comparison — the one `If-None-Match` is
    specified to use — and that is not a technicality here. `GZipMiddleware`
    (D31, added the previous session) downgrades a strong `ETag` to `W/"..."`
    on any response it actually compresses, so the value this app hands out
    and the value the client hands back can differ by that prefix. A strong
    byte-for-byte comparison would therefore never match, on exactly the
    responses that compressed — a fix that looks complete, sets every
    header, and silently returns a full body every time.

    Measured on a live server, because the obvious guess is wrong: JPEG
    photo bytes *do* compress enough (~2% on a real 359 KB photo) for the
    middleware to keep the compressed response, so this is the normal case
    for a browser, not an edge one. A 304 takes the other branch — it is
    too short for GZipMiddleware to touch — so the app can hand out the
    weak form on a 200 and the strong form on the 304 that follows. Weak
    comparison is what makes both directions match.
    """
    from django.utils.http import parse_etags

    if not if_none_match_header or not etag:
        return False
    candidates = parse_etags(if_none_match_header)
    if "*" in candidates:
        return True
    target = _without_weak_prefix(etag)
    return any(_without_weak_prefix(c) == target for c in candidates)


def serve_image(request, *, stored_content_type, digest, load_bytes):
    """A conditional response for one stored image.

    `load_bytes` is a callable, not bytes, and that is the entire point: on
    a validator hit it is never called, so a 304 costs one small metadata
    row and never reads the blob column. Callers pass a lambda that fetches
    the bytes explicitly (a `values_list`, matching the convention
    apps/accounts/blobs.py sets out) rather than touching a deferred
    attribute, so the read is visible in the code rather than issued
    invisibly by an attribute access.

    A row with no digest — nothing writes one today, but a future migration
    path might — degrades to exactly the old behaviour: a full body, no
    ETag, still `Cache-Control`.

    Splitting the metadata read from the byte read opens a window the old
    single-query version did not have: the row can be deleted, or its
    property flipped private, between the two. That is microseconds wide
    and needs a concurrent delete, but the failure would be a 500 where
    the truth is "no such photo" — so the miss path answers 404 instead,
    which is what the very next request would say anyway.
    """
    from django.core.exceptions import ObjectDoesNotExist
    from django.http import Http404, HttpResponseNotModified

    etag = f'"{digest}"' if digest else ""
    if etag and etag_matches(request.headers.get("If-None-Match"), etag):
        response = HttpResponseNotModified()
        # A 304 must repeat the validating headers, or a cache that stored
        # the original has nothing to refresh its own entry with.
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = IMAGE_CACHE_CONTROL
        return response

    try:
        data = load_bytes()
    except ObjectDoesNotExist:
        raise Http404("That image is no longer available.")

    response = image_response(data, stored_content_type)
    if etag:
        response.headers["ETag"] = etag
    return response
