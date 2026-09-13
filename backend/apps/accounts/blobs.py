"""Which columns hold image bytes, and why every query that doesn't serve
those bytes has to defer them.

Habitat stores images **in the database**, not in object storage (a
decided, documented choice — see /docs/data-model-notes.md). That puts
four `BinaryField` columns in the schema, and two of them sit on *main*
tables rather than on a side table:

    Organization.theme_header_image   (models.py)
    Property.theme_header_image       (models.py)
    ActivityPhoto.image               (apps/activities/models.py)
    SightingPhoto.image               (apps/sightings/models.py)

Every serializer in this app is scrupulous about never *serializing*
those bytes — `OrganizationSerializer`/`PropertySerializer` expose a
`has_theme_header_image` boolean instead, and the two photo serializers
expose a `url` pointing at the dedicated byte-serving view. All of that
is true, and it is exactly what hid this problem for the life of the
project: a reader who checks the serializer concludes the blob is
handled. **A serializer decides what goes out; it has no say in what the
queryset loads.** Deferring is the other half, and nothing was doing it.

What that cost, measured (see the 2026-09-13 task-log entry): a themed
property carrying a 5 MB banner, listed alongside 100 of its own
sightings, produced 100 distinct Python `Property` objects each holding
its own copy of those bytes — half a gigabyte to render a JSON array
that contains the banner's *boolean*. Django does not dedupe a
`select_related` target across rows, and the org-wide list pages are not
paginated, so nothing bounds it.

Three things about the fix are easy to get wrong, so they are pinned
here rather than left to be re-derived:

1. **This cannot be centralized into `PropertyManager`.** That is the
   obvious move — `Property.objects` already filters soft-deleted rows,
   so why not defer there too? Because `select_related("property")` does
   **not** consult the related model's default manager; it compiles to a
   join and pulls that table's columns directly. A manager-level defer
   would therefore miss the per-row duplication above, which is the
   sharpest case there is. The deferral has to be written on the
   *outer* queryset, as `defer("property__theme_header_image")`, which is
   why these helpers are called explicitly at each list site instead of
   being hidden in a manager. (Same Django semantic that
   `apps/public_site/views.py` has to get right for soft-delete filtering
   — a join does not go through a manager. It bites in both directions.)

2. **Defer the blob, never the `_content_type` CharField beside it.**
   `get_has_theme_header_image` reads the content type to decide its
   boolean. The column is tiny and it *is* on the read path.

3. **Never reach for `.only()` instead.** Listing the fields you want
   defers everything else, including columns the serializer does read —
   and Django answers a touched deferred field with a fresh query *per
   row*. The JSON comes back byte-identical, so an outcome test cannot
   tell that fix from this one; only a query-count assertion can. The
   tests for this live in `apps/accounts/tests.py`.
"""

# Same field name on Organization and on Property (both get it from
# apps/accounts/theming.py's shared set of theme knobs).
THEME_IMAGE_BLOB = "theme_header_image"

# Same field name on ActivityPhoto and on SightingPhoto.
PHOTO_IMAGE_BLOB = "image"


def defer_theme_image(qs, path=""):
    """Drop the theme banner bytes from what `qs` loads.

    `path` names a `select_related` ancestor to defer *through* — e.g.
    `defer_theme_image(qs, "property")` on an Activity/Sighting queryset,
    which is the form that works across a join (confirmed by measurement,
    not assumed). Omit it for a queryset of Organizations or Properties
    themselves.

    Only ever call this where nothing downstream reads the bytes. Every
    site that does read them (the byte-serving views, and the upload and
    delete paths) builds its own single-object lookup and does not go
    through these querysets.
    """
    prefix = f"{path}__" if path else ""
    return qs.defer(f"{prefix}{THEME_IMAGE_BLOB}")


def defer_photo_image(qs):
    """Drop the photo bytes from what `qs` loads — for the four photo
    *list* endpoints, whose serializers emit a URL and never the bytes.
    The matching `<photo>_image` view fetches its own row and is
    unaffected."""
    return qs.defer(PHOTO_IMAGE_BLOB)
