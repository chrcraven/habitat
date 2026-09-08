"""Parsing integer query parameters without handing the raw string to the
database layer.

This module exists because four list endpoints took an id straight from the
query string and dropped it into a queryset:

    property_id = self.request.query_params.get("property")
    if property_id:
        qs = qs.filter(property_id=property_id)

A `?property=` value is just text — nothing in a URL constrains it, unlike a
*path* parameter, where this project's `<int:...>` converters reject a
non-numeric before any view runs (which is why every one of the ~40
`get_object_or_404` path-parameter lookups in this repo is already safe, and
why only the query parameters needed this). So `?property=abc` reached the
database driver, which raised `ValueError` turning it into an integer, and
nothing converted that into a response: DRF's exception handler returns
`None` for it, so it surfaced as an unhandled **500**.

That is not a hypothetical request shape — **the app itself sends one.**
`/properties/abc` is a real frontend route; `PropertyMapPage` did
`Number(id)` with no guard and immediately fired four requests with the
result, and the API client's `withQuery` skips only `undefined`, so
`String(NaN)` went on the wire as the literal `NaN`. One mistyped or stale
property URL therefore produced three 500s, where "no such property" was the
truth.

**Why 400 rather than 404 at the filter call sites.** The rule this module
follows is: *match what a valid-but-nonexistent id already does there.*

* On a **filter** (`?property=`, `?assigned_to=`), a valid id that matches
  nothing deliberately returns `200` with an empty list — the parameter
  narrows a collection, it doesn't identify a resource. So a 404 would be
  the wrong shape, and 400 is the honest answer: the parameter really is
  malformed. This matches `?blooming_on=`, the one query parameter in the
  repo that already validated its input (`apps/species/views.py`).
* On a **lookup** (`apps/pages/views.py`, which resolves `?property=` to a
  real `Property` and 404s when it belongs to another org), a malformed id
  is "no such property" — so that call site stays a 404 and simply switches
  to DRF's `get_object_or_404`, which catches `(TypeError, ValueError,
  ValidationError)` where `django.shortcuts`' catches only `DoesNotExist`.
  That difference is the whole reason the DRF-generated detail routes were
  already fine while that one hand-written lookup was not.

Keep `int_query_param` returning `None` for both an absent and an empty
parameter: `?property=` (empty) has always meant "no filter", and callers
must therefore test `is not None` rather than truthiness, so that an
explicit `?property=0` still filters (to nothing) exactly as it did before.
"""

from rest_framework.exceptions import ValidationError


def int_query_param(request, name):
    """Return `?<name>=` as an int, or None if it was absent or empty.

    Raises DRF's ValidationError (a 400) if it was present but not an
    integer, rather than letting the string reach the database layer and
    500 there.
    """
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be a whole number."})
