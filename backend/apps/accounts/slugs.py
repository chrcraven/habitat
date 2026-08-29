"""Slug generation for public vanity URLs.

Organizations get one globally-unique slug (`/public/<org-slug>`); each
property gets a slug that only has to be unique *within its own org*
(`/public/<org-slug>/<property-slug>`) — see /docs/open-questions.md
("Vanity slug URLs") for the decided shape.

Generation is auto-slugify-from-name with a numeric suffix on collision
(`north-meadow`, `north-meadow-2`, …) rather than reject-and-ask, so a
brand-new org/property is always immediately reachable by a readable URL
without the user having to pick one. Admins can still override the slug
by hand on the edit forms; that path validates uniqueness and rejects a
clash (see the serializers) instead of silently suffixing.
"""

from django.utils.text import slugify

# Slugs that would collide with an existing static segment of the public
# URL space (`/public/org/<id>`, `/public/properties/<id>`) or otherwise
# be ambiguous. An org may not take one of these as its top-level slug.
RESERVED_ORG_SLUGS = {"org", "organizations", "properties", "property", "public", "api"}


def _base_slug(name, fallback):
    base = slugify(name or "")
    return base or fallback


def unique_slug(model_cls, name, *, fallback, filters=None, exclude_pk=None, reserved=None):
    """Return a slug for `name` that's unique among `model_cls` rows
    matching `filters` (a dict of extra queryset filters, e.g. the owning
    organization for a property), excluding `exclude_pk` (the row being
    updated, so it doesn't collide with itself).

    `reserved` is an optional set of slugs to skip entirely (used for the
    org-level reserved names above).
    """
    filters = filters or {}
    reserved = reserved or set()
    base = _base_slug(name, fallback)

    candidate = base
    n = 2
    while True:
        clash = not candidate or candidate in reserved
        if not clash:
            qs = model_cls.objects.filter(slug=candidate, **filters)
            if exclude_pk is not None:
                qs = qs.exclude(pk=exclude_pk)
            clash = qs.exists()
        if not clash:
            return candidate
        candidate = f"{base}-{n}"
        n += 1
