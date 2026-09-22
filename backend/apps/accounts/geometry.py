"""Letting a list endpoint leave out the geometry its caller never draws.

Habitat's three record types are all served as GeoJSON by
`GeoFeatureModelSerializer` — `Property.boundary`, `Activity.geometry`
and `Sighting.location`. That is the right shape for a map. It is the
wrong shape for the org-wide list screens, which draw no map at all and
pay for the coordinates anyway.

# The measurement that makes this worth doing

Coordinates are high-entropy digits. Compression (D31's first half,
`GZipMiddleware`, built 2026-09-14) squeezes the repetitive JSON keys
around them to almost nothing and barely touches the numbers — so
geometry is a *minority* of the raw payload and the large majority of
the compressed one. Measured on real HTTP at 10,000 activities with
6-vertex polygons at 7-decimal precision:

    with geometry    6,423,457 raw    679,896 gzipped
    ?geometry=omit   4,368,935 raw    116,693 gzipped
    saved                 32.0%          82.8%

(D31's original figures — 6.1 MB / 868 KB / 62 KB — were measured
against the live host's own 4-5 vertex rows. The raw number reproduces;
the compressed ones differ, because what compresses is a property of the
coordinates rather than of this code. Quote whichever fixture you mean.)

The list endpoints are org-wide and unpaginated (D30/D31), so nothing
bounds that.

# The rule

**Omitting geometry is opt-in, per request, and only on `list`.**

Opt-in matters because these serializers are shared with
`apps/public_site/` — the same classes are served to anonymous visitors
under `AllowAny` (see apps/accounts/attribution.py, which exists because
of the same sharing). A default of "omit" would silently change
anonymous output; a default of "include" means every caller that does
not ask is byte-identical to before.

`list`-only matters for a sharper reason: a serializer with no geometry
field cannot *write* one. Honouring the parameter on `create`/`update`
would mean a `POST` that silently dropped the shape the user just drew,
and a `PATCH` whose response told the frontend the record's geometry was
now null — which `ActivityFormPage` would then re-submit (D29). The
viewsets therefore check `self.action == "list"`, the same narrowing
`apps/pages/views.py` applies to its own `?property=` filter.

# Both halves are required, and each alone is a different wrong fix

Serializing less and loading less are separate mechanisms, and doing
only one of them is worse than doing neither:

1. **`.defer()` alone.** The column stops being selected, and then
   `to_representation` reads it anyway — `GeoFeatureModelSerializer`
   looks up `Meta.geo_field` unconditionally — so Django issues a fresh
   query *per row* to fetch the value it was told to skip. The response
   is **byte-identical**, so no outcome test can tell this from the real
   fix; only a query-count assertion can. This is the trap the
   2026-09-15 session recorded when it declined to build this item, and
   it is the same shape as `blobs.py`'s "never reach for `.only()`".

2. **`Meta.geo_field = None` alone.** The library documents this ("Set
   it to None if there is no geometry") and it does exactly what it
   says: `feature["geometry"]` becomes `None` without the instance
   being touched. But the field is *still listed in* `Meta.fields`, and
   `to_representation` only skips fields it has already processed — so
   the geometry falls through into `get_properties`, which reads it,
   serializes it, and emits the whole thing again under
   `properties.geometry`. The payload gets *bigger*, and on a deferred
   queryset it also pays case 1's per-row query. Both halves of the
   subclass below — `geo_field = None` **and** dropping the field from
   `fields` — are load-bearing.

3. **The serializer change alone, with no `.defer()`.** This one is
   genuinely correct in its output and still reads every coordinate out
   of the database and across the wire into Python. It saves the
   client's bytes and none of the server's. Invisible in the response,
   visible only in the columns the query selects.

# Why `Property` needed one more part than the other two

`Activity.geometry` and `Sighting.location` are non-null columns, so
`geometry: null` on one of those rows is unambiguous: it can only mean
"you asked for it to be left out". **`Property.boundary` is nullable** —
the model docstring says so explicitly, because a property can be named
before its boundary is drawn — and `PropertiesPage` renders exactly that
distinction ("Boundary drawn" / "No boundary drawn yet"). Omitting
geometry there without more would collapse *not sent* into *not drawn*
and silently mislabel every property that has one, which is D47's lesson
(ask what a value's empty case means before consuming it) and D39's.

So the row carries the distinction separately, as `has_boundary` — and
it has to be a **database annotation** (`annotate_has_boundary` below),
not a Python check. `obj.boundary is not None` on a deferred instance is
case 1 above wearing a different hat: it reads the column back one row
at a time, so the "cheap" boolean costs a query per property *and* still
drags every coordinate out of Postgres. Strictly worse than not omitting
at all, and invisible in the response.

`IS NOT NULL` names the column without selecting its value, so the
coordinates stay in the database. That is also why the mechanism tests
match a **whole quoted column name** in the SELECT list rather than
grepping the statement — `"boundary" in sql` is true of the annotation
itself, which is D27's substring trap sitting directly on top of the
thing being asserted.
"""

from django.db.models import BooleanField, ExpressionWrapper, Q
from rest_framework.exceptions import ValidationError

# The query parameter, and its one accepted value. An allowlist rather
# than a truthiness check: `?geometry=false` and `?geometry=no` would
# both read as "leave it out" to a caller and as "not the magic string"
# to a truthiness check, and the caller would never find out. Anything
# unrecognised is a 400, matching `?blooming_on=` and
# apps/accounts/query_params.py — a malformed parameter is answered, not
# ignored.
GEOMETRY_PARAM = "geometry"
GEOMETRY_OMIT = "omit"

_INVALID = f'The only accepted value is "{GEOMETRY_OMIT}". Leave it off to include geometry.'


def omit_geometry_requested(request):
    """True when this request asked for geometry to be left out.

    Absent or empty means no, so the default is always today's behaviour.
    Raises DRF's ValidationError (a 400) on any other value.
    """
    raw = request.query_params.get(GEOMETRY_PARAM)
    if raw is None or raw == "":
        return False
    if raw != GEOMETRY_OMIT:
        raise ValidationError({GEOMETRY_PARAM: _INVALID})
    return True


# The annotation alias, and the serializer field name, deliberately the
# same string: `PropertySerializer.get_has_boundary` reads the annotation
# straight off the instance by this name.
HAS_BOUNDARY = "has_boundary"


def annotate_has_boundary(queryset, geo_field):
    """Carry "is there a shape?" as its own column.

    Needed wherever a *nullable* geo column may be omitted, so that
    `geometry: null` stops having to mean two different things. See this
    module's docstring — computing it in Python instead is case 1.

    **Pair this with `defer_geometry` and nothing else.** An annotation
    is evaluated when the row is fetched, so it describes the row as it
    was *then*: apply it to the queryset behind an `update` and the
    response to a PATCH that draws a boundary reports the answer from
    before the write. That was measured, not reasoned about — an earlier
    version of this annotated every action and a test for an unrelated
    wrong fix went red. Wherever the column is actually loaded there is
    nothing to gain here anyway, because the value itself is in hand.
    """
    return queryset.annotate(
        **{
            HAS_BOUNDARY: ExpressionWrapper(
                Q(**{f"{geo_field}__isnull": False}), output_field=BooleanField()
            )
        }
    )


def defer_geometry(queryset, geo_field):
    """Stop the geometry column being selected.

    Half of the fix — pair it with `without_geometry` on the serializer,
    or the deferred column is read back one row at a time. See this
    module's docstring, case 1.
    """
    return queryset.defer(geo_field)


_cache = {}


def without_geometry(serializer_class):
    """A subclass of `serializer_class` that emits `"geometry": null` and
    never reads the geometry column.

    Built here rather than written out per serializer because there are
    three geo serializers and two attribution subclasses over them, and
    the two things that make it correct (see this module's docstring,
    case 2) are exactly the two things a hand-written copy would get
    wrong in one of them and not the others.

    The generated Meta gets its own `fields` **list**, never the
    parent's: `GeoFeatureModelSerializer.__init__` appends to
    `Meta.fields` in place, so sharing the list would let the child's
    construction mutate the base serializer the public site uses.
    """
    cached = _cache.get(serializer_class)
    if cached is not None:
        return cached

    parent_meta = serializer_class.Meta
    geo_field = parent_meta.geo_field
    meta = type(
        "Meta",
        (parent_meta,),
        {
            # Emits `"geometry": null` straight from `to_representation`
            # without touching the instance.
            "geo_field": None,
            # ...and this is what stops it reappearing under
            # `properties`. A new list, for the reason in the docstring
            # above.
            "fields": [name for name in parent_meta.fields if name != geo_field],
        },
    )
    subclass = type(
        f"{serializer_class.__name__}WithoutGeometry",
        (serializer_class,),
        {"Meta": meta, "__doc__": without_geometry.__doc__},
    )
    _cache[serializer_class] = subclass
    return subclass
