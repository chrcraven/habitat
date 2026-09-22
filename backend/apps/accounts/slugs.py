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

# The same rule one URL segment deeper, for `/public/<org>/<property>`.
# A property slug sits at position 3, where the frontend's route table
# (frontend/src/App.tsx) already spends two literal segments:
#
#     /public/:orgSlug/explore            -> the org's Explore view
#     /public/:orgSlug/pages/:pageSlug    -> one of the org's own pages
#
# react-router ranks a literal segment above a dynamic one, so without
# this set those two literals win and the *property* is what gets
# shadowed. Measured on the pinned react-router (6.30.4) against the real
# route table, the two collisions are disjoint and complementary, which
# is why both names are here and why handling only the obvious one is not
# enough:
#
#   - a property slugged "explore" loses its **root**
#     (`/public/o/explore` serves the org's Explore view) and keeps its
#     children (`/public/o/explore/pages/p1` resolves correctly);
#   - a property slugged "pages" keeps its **root** and loses its
#     **children** — `/public/o/pages/p1` resolves to the
#     *organization's* authored page `p1`, so if the org has one the
#     visitor is served a different, real page with a 200 and no error.
#
# That second case is the dangerous one, and it is why this set is NOT
# apps.pages.RESERVED_PAGE_SLUGS. That set is `{"explore"}` only —
# correct for a page, whose slug sits at position 4 where "pages" is
# harmless — so importing it here looks like tidy reuse and leaves the
# silently-wrong half live. See D53 in docs/open-questions.md.
RESERVED_PROPERTY_SLUGS = {"explore", "pages"}


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
