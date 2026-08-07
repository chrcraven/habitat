# Data Model Notes

This is early, deliberately unlocked thinking about what Habitat's core
records need to capture. It's written as open questions and options, not a
schema. Nothing here should be read as decided — see `open-questions.md`
for the running list of things this doc raises but doesn't resolve.

## Activity record

An "activity" is the individual land manager's core unit of work: a
seeding, planting, treatment, or other intervention. See
`use-cases.md` (a) for the motivating story.

Likely needed:

- **Activity type.** Seeding, planting, treatment, intervention (general
  catch-all), possibly others (removal, monitoring-only, maintenance?).
  Open question: fixed enum vs. extensible/user-defined types — a large
  organization may want treatment categories a single homeowner never
  needs, and vice versa.
- **Status / lifecycle.** At minimum, **planned** vs. **done** — this
  distinction is a hard requirement, because planned items need to feed a
  public "upcoming/in-progress work" view, not just a completed-work log.
  Beyond that pair, the exact state set is undecided. Candidates: planned →
  in-progress → done, plus maybe cancelled/abandoned, or on-hold. Options
  range from a simple fixed enum to a small configurable workflow (useful
  for an organization with its own process, overkill for a single
  homeowner). See `open-questions.md`.
- **Geometry, not just a point.** The area an activity/intervention applies
  to is a user-drawn shape — polygon, rectangle, or other geometry — not a
  single coordinate. This is a first-class modeling difference from
  sightings (below) and has real implications for storage and querying
  (see "Geospatial data handling" section).
- **Date(s).** At least one date (when planned for / when done). Possibly a
  range (start/end) for multi-day or ongoing work, and a separate
  "recorded on" timestamp vs. "activity date" — those aren't always the
  same (e.g., logging a planting from three days ago).
- **Species / treatment details.** For a planting or seeding: species
  (single or multiple, with quantities?). For a treatment: what was
  treated (target species, e.g., an invasive) and method/product used.
  **Direction: structured, reference-backed species data** — species
  fields should resolve against a reference list/taxonomy (e.g., a
  regional native plant database, or an existing standard like GBIF or
  USDA PLANTS) rather than staying free text, since that's what makes
  species data useful across the platform later (public display,
  filtering, and linking a sighting like Field Bindweed to the treatment
  that addresses it — see below). Free text likely still has a role as a
  fallback/detail field alongside the structured pick. Which reference
  source(s) to use is still open — see `open-questions.md`.
- **Photos / media.** One activity record should support multiple photos,
  attachable at creation or added later (e.g., before/after). Likely also
  needs basic metadata per photo (captured date, maybe which
  planned-vs-done state it corresponds to).
- **Notes.** Freeform text for anything structured fields don't capture.
- **Ownership / linkage.** Which account and which property/parcel (see
  below) the activity belongs to, and who (which user, under a
  multi-contributor account) logged or last edited it.
- **Public visibility.** **Decided: activity records are public by
  default.** The public-facing view (`use-cases.md` (c)) is a core part of
  the vision, not an opt-in afterthought. Still open: whether there's any
  per-record or per-field override to make something private (e.g., a
  sensitive location), and whether that override is available from Phase 2
  or added later — see `open-questions.md`.

## Sighting record

A "sighting" (e.g., a wildlife observation) is deliberately modeled
differently from an activity — see `use-cases.md` (b).

Likely needed:

- **Species.** What was observed — same structured/reference-backed
  direction as activity records (above). Sightings and activities should
  almost certainly share the same species reference list/taxonomy, since
  that shared reference is exactly what makes linking a sighting to a
  responding activity (below) meaningful — e.g., a Field Bindweed sighting
  and a Field Bindweed treatment referring to the same species record, not
  two independently-typed strings.
- **Point location.** Simple device-location capture — a single
  coordinate, not a drawn shape. This is the key structural difference from
  activity records.
- **Timestamp.** When the sighting occurred (which may differ from when it
  was logged, if entered after the fact).
- **Photos.** Same general need as activities — one or more photos
  attachable to the record.
- **Notes.** Freeform text, same as activities.
- **Public visibility.** Public by default, consistent with activity
  records — but sightings raise a sharper version of the privacy question:
  reports of sensitive or at-risk species (e.g., an endangered species'
  exact location) are a well-known case where public geolocation data can
  cause real harm (poaching, disturbance, collection). This likely needs a
  private/obscured-location option — per-sighting, per-species (an
  auto-flagged sensitive-species list), or left to the account manager's
  judgment. Not resolved — see `open-questions.md`.

### Do sightings and activities share a data model?

**Decided: separate tables/record types.** Sightings and activities have
different location models (point vs. geometry) and different lifecycles (a
sighting has no "planned" state), so they don't share a single schema.
They still share conventions — photo attachment, account/property linkage,
species reference, visibility — even as separate types.

**But they need an explicit relationship: sightings can lead to
activities.** A sighting that identifies a problem — e.g., someone logs a
Field Bindweed (an invasive species) sighting — is exactly the kind of
input that should be able to inform, and later be linked to, the planned
or completed intervention that addresses it (see `use-cases.md` (f)). This
applies to the account owner's own sightings well before any public
submission mechanism exists (Phase 5), and is part of why public input
matters at all: it's the "reported → responded to" loop the public-facing
view can eventually show.

Open questions this raises (tracked in `open-questions.md`):

- Is the link one sighting → one activity, or many-to-many (one
  intervention might address several reported sightings; one sighting
  might relate to more than one activity over time, e.g. an initial
  treatment and a follow-up)?
- Is linking manual (a land manager reviews a sighting and attaches it to
  an activity) or could it ever be suggested/automatic (e.g., by species +
  proximity)? Manual is almost certainly the right starting point.
- Does a linked sighting's own status change once addressed (e.g.,
  "reported" → "actioned"), or does the sighting stay unmodified and the
  link itself carries that meaning?
- Should the public-facing view surface this link (e.g., "reported by a
  visitor, treated on this date")? That pairing is a good showcase of the
  public-input → management-action loop the project is ultimately aiming
  for.

No link schema decided yet — just establishing that the relationship needs
to exist, and that it's a reason (not just a side effect) for keeping
sightings and activities as separate, explicitly-linked record types.

## Accounts / ownership, single individual → multi-user organization

**Decided: one Habitat instance/account corresponds to one organization or
manager.** A single homeowner's account today happens to have one
contributor, but the account itself is not a "single-user" type — it's an
organization that currently has a headcount of one. There is no separate
"individual account" type with different capabilities, and no migration
step required to "become" an organization: **an org account supports
multiple users from the moment it's created**, whether or not it uses that
capability right away. The account model is the same shape whether it
represents one person managing one yard or a land trust managing many
properties and staff. This resolves the earlier open question of
individual-vs-org account types: there's one account/org model, not two,
and it holds up across the full range in `use-cases.md` (a single
homeowner, another individual homeowner, and a large organization — use
case d).

Rough shape under consideration:

- **Account (organization).** The top-level owner of data. Every Habitat
  account is, structurally, an organization — a single homeowner's account
  and a land trust's account are the same kind of thing, just with
  different numbers of properties and contributors. Open question: how
  much organization-management UI (invites, roles, multiple properties)
  gets exposed to a one-person account by default — the underlying model
  should be uniform, but the *interface* for a single homeowner shouldn't
  force them through org-management screens they don't need yet.
- **Property / parcel.** A piece of land with a boundary, owned by an
  account. **Multiple properties are supported under a single account from
  the start** — a single homeowner might have exactly one property (their
  own yard), while a land trust has many. Activities and sightings are
  linked to a property, and through it to the owning account.
- **Users / contributors.** One or more people who can log activity under
  an account — **multi-user support is a property of every account, not a
  separate tier.** The author's own account may have just one contributor
  (the author) at first, but a second contributor (a spouse, a helper) can
  be added to that same account at any time, with no change in account
  type. For a larger organization, this is used more heavily from day
  one: multiple staff/volunteers, not all with the same access.
- **Permissions.** Still open in detail — see `open-questions.md`. Likely
  needs at least: who can create/edit records, and at what scope
  (account-wide vs. specific properties). A larger organization probably
  needs per-property permission scoping (use case d); a single-person
  account needs approximately none of this complexity surfaced to them,
  even though the underlying model supports it.

The guiding constraint remains: the single-homeowner case should stay
simple to use — no organization-management UI forced on someone with one
property and one contributor — while the same account/property/user
structure supports an organization with many properties and many
contributors without a rearchitecture. With the account model now settled
as "one account = one org, currently at whatever headcount it has," the
remaining work is UI/UX simplification for the small case (hiding
org-management complexity a one-person account doesn't need yet) and
permission-model detail for the large case — not the underlying structure,
and not whether multi-user support exists at all.

## Geospatial data handling (first-class concern)

Storing and querying arbitrary user-drawn shapes alongside simple points is
a core technical challenge, not an incidental one, and needs to work at
both ends of the scale range:

- **Small scale:** one yard, a handful of small polygons (planting beds,
  treatment areas), a handful of point sightings. Low volume, but the
  drawing/editing UX and query correctness still need to be solid — this is
  the first real use case (Phase 1).
- **Large scale:** many properties, some potentially large tracts, with
  many activity geometries and many sightings accumulated over time.
  Needs to support:
  - Efficient storage of arbitrary polygon/rectangle geometry (not just
    bounding boxes).
  - Spatial querying — e.g., "activities within this area," "sightings
    near this point," "everything within a property's boundary" — with
    reasonable performance as the number of records grows.
  - Rendering many geometries on a map performantly (relevant to both the
    public map view, use case (c), and an organization-wide overview, use
    case (d)).
  - API-level geospatial filtering for downstream consumers (use case (e)),
    e.g., bounding-box or radius queries.
  - Interoperability with standard GIS formats and tools — the ability to
    export (and eventually import) data as GeoJSON, Shapefile, KML, or
    GeoPackage, so records logged in Habitat can be opened in QGIS,
    ArcGIS, or other GIS software, and so existing GIS data (e.g., a
    property boundary survey, an organization's existing parcel data) can
    be brought into Habitat rather than redrawn by hand.

**Decided: PostGIS is the geospatial engine.** All candidate stacks in
`tech-stack-options.md` converge on PostgreSQL + PostGIS, and that's now
treated as settled rather than provisional. It natively handles both point
and polygon geometry, supports spatial indexing/querying at scale, and —
via functions like `ST_AsGeoJSON`/`ST_AsKML` and tools like GDAL/OGR
(`ogr2ogr`) — gives a direct path to the GIS-interoperability requirement
above. What's still open is the application framework built on top of it
(see `tech-stack-options.md`).
