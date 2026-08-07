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
  Open question: how structured should this be — free text, a species
  picker backed by some reference list (e.g., regional native plant
  database), or both allowed depending on user need?
- **Photos / media.** One activity record should support multiple photos,
  attachable at creation or added later (e.g., before/after). Likely also
  needs basic metadata per photo (captured date, maybe which
  planned-vs-done state it corresponds to).
- **Notes.** Freeform text for anything structured fields don't capture.
- **Ownership / linkage.** Which account and which property/parcel (see
  below) the activity belongs to, and who (which user, under a
  multi-contributor account) logged or last edited it.
- **Public visibility.** Given the public-facing use case, some notion of
  whether an activity (or fields within it) is visible publicly, private to
  the account, or something in between. Not yet defined — see
  `open-questions.md`.

## Sighting record

A "sighting" (e.g., a wildlife observation) is deliberately modeled
differently from an activity — see `use-cases.md` (b).

Likely needed:

- **Species.** What was observed — same open question as above about
  free text vs. structured/reference-backed species data, and whether
  sightings and activities should share a species reference list even if
  their record structures differ.
- **Point location.** Simple device-location capture — a single
  coordinate, not a drawn shape. This is the key structural difference from
  activity records.
- **Timestamp.** When the sighting occurred (which may differ from when it
  was logged, if entered after the fact).
- **Photos.** Same general need as activities — one or more photos
  attachable to the record.
- **Notes.** Freeform text, same as activities.

### Do sightings and activities share a data model?

Open question (also tracked in `open-questions.md`): sightings and
activities clearly need different location models (point vs. geometry) and
probably don't share a status lifecycle (a sighting doesn't have a
"planned" state). Options:

1. Fully separate tables/types, sharing nothing but conventions (photo
   attachment pattern, account/property linkage).
2. A shared base "record" concept (account, property, timestamp, photos,
   notes, visibility) with type-specific extensions for location model and
   status.
3. One polymorphic table with a location field that's sometimes a point and
   sometimes a geometry, differentiated by record type.

No preference recorded yet — this affects both the database schema and the
future API shape (use case (e)), so it's worth resolving before Phase 1
implementation goes very far.

## Accounts / ownership, single individual → multi-user organization

The account model needs to hold up across the full range in `use-cases.md`:
a single homeowner (use case a/b), another individual homeowner (same
shape, different data), and a large organization with many
properties/parcels and many contributors (use case d).

Rough shape under consideration, not decided:

- **Account** — the top-level owner of data. Could be an individual account
  or an organization account. Open question: are these two distinct account
  *types* with different capabilities, or is an "individual" just an
  organization of one, with the same underlying structure throughout? The
  latter is architecturally appealing (one model, no special-casing) but
  may be more machinery than a single homeowner needs or wants to see.
- **Property / parcel** — a piece of land with a boundary, owned by an
  account. A single-user account might have exactly one property (the
  user's own yard) or a few. An organization account likely has many.
  Activities and sightings are linked to a property (and, implicitly,
  through it to an account).
- **Users / contributors** — one or more people who can log activity under
  an account. For an individual account this may just be one person (the
  owner) initially, but shouldn't structurally block adding a second person
  later (a spouse, a helper). For an organization, this is core: multiple
  staff/volunteers, not all with the same access.
- **Permissions.** Undecided in any detail — see `open-questions.md`. Likely
  needs at least: who can create/edit records, and at what scope
  (organization-wide vs. specific properties). A large organization
  probably needs per-property permission scoping (use case d); a single
  homeowner needs approximately none of this complexity exposed to them.

The guiding constraint: the account/property/permission structure should be
designed so the single-homeowner case is simple to use (no
organization-management UI forced on someone with one yard), while the same
underlying structure supports an organization with many properties and
contributors without a rearchitecture. Whether that's achieved by having
one unified model (organization-of-one) or by two account types built on a
shared foundation is an open question.

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

This has direct implications for the tech stack (see
`tech-stack-options.md`), which evaluates candidates specifically against
geospatial storage/querying needs rather than treating it as a detail to
figure out later.
